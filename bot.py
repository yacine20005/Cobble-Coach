import os
import json
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
import google.genai as genai

from lol_coach.riot_api import build_headers, get_puuid, get_match_ids
from lol_coach.export_service import collect_games_data

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GAME_NAME = os.getenv("DEFAULT_GAME_NAME", "")
DEFAULT_TAG_LINE = os.getenv("DEFAULT_TAG_LINE", "")
TOTAL_GAMES = int(os.getenv("TOTAL_GAMES", "50"))
REGION_ROUTING = os.getenv("REGION_ROUTING", "europe")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt_lol.md")


def read_prompt_template() -> str:
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(games_data: list[dict]) -> str:
    template = read_prompt_template()
    data_text = json.dumps(games_data, ensure_ascii=True)
    marker = "[DATA]"
    if marker in template:
        return template.replace(marker, data_text)
    return f"{template}\n\n{data_text}"


def chunk_text(text: str, limit: int = 1900) -> list[str]:
    chunks: list[str] = []
    current = []
    current_len = 0

    for line in text.splitlines():
        line_len = len(line) + 1
        if current_len + line_len > limit:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def extract_gemini_text(response: genai.types.GenerateContentResponse) -> str:
    if response.text:
        return response.text

    text_parts: list[str] = []
    finish_reasons: list[str] = []

    for candidate in response.candidates or []:
        if candidate.finish_reason is not None:
            finish_reasons.append(str(candidate.finish_reason))

        content = candidate.content
        if not content or not content.parts:
            continue

        for part in content.parts:
            if isinstance(part.text, str) and part.text:
                text_parts.append(part.text)

    if text_parts:
        return "".join(text_parts)

    details: list[str] = []
    prompt_feedback = response.prompt_feedback
    if prompt_feedback is not None:
        details.append(f"prompt_feedback={prompt_feedback.model_dump(exclude_none=True)}")
    if finish_reasons:
        details.append(f"finish_reasons={finish_reasons}")
    if response.candidates:
        details.append(f"candidates={len(response.candidates)}")

    detail_suffix = f" Details: {'; '.join(details)}" if details else ""
    raise ValueError(f"Gemini returned no text content.{detail_suffix}")


def generate_gemini_analysis(prompt: str) -> str:
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    response = genai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return extract_gemini_text(response)


class LolCoachBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()


client = LolCoachBot()


@client.tree.command(name="coach", description="Analyze recent games and provide coaching insights with Gemini AI.")
@app_commands.describe(game_name="Riot game name", tag_line="Riot tagline")
async def coach_command(
    interaction: discord.Interaction, game_name: str | None = None, tag_line: str | None = None
) -> None:
    await interaction.response.defer(thinking=True)

    if not DISCORD_BOT_TOKEN or not RIOT_API_KEY or not GEMINI_API_KEY:
        await interaction.followup.send("Missing API keys. Check .env configuration.")
        return

    game_name = game_name or DEFAULT_GAME_NAME
    tag_line = tag_line or DEFAULT_TAG_LINE

    if not game_name or not tag_line:
        await interaction.followup.send(
            "Please provide game_name and tag_line or set defaults in .env."
        )
        return

    try:
        headers = build_headers(RIOT_API_KEY)
        puuid = await asyncio.to_thread(get_puuid, game_name, tag_line, headers, REGION_ROUTING)
        match_ids = await asyncio.to_thread(get_match_ids, puuid, headers, TOTAL_GAMES, 100, REGION_ROUTING)
    except Exception as e:
        await interaction.followup.send(f"Failed to fetch match list: {e}")
        return

    games_data = await asyncio.to_thread(
        collect_games_data, 
        match_ids, 
        puuid, 
        headers, 
        REGION_ROUTING, 
        1.5, 
        TOTAL_GAMES
    )

    if not games_data:
        await interaction.followup.send("No games data found for this player.")
        return

    try:
        prompt = build_prompt(games_data)
        analysis_text = await asyncio.to_thread(generate_gemini_analysis, prompt)
    except Exception as e:
        await interaction.followup.send(f"Gemini request failed: {e}")
        return

    chunks = chunk_text(analysis_text)
    for chunk in chunks:
        await interaction.followup.send(chunk)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        raise SystemExit("Missing DISCORD_BOT_TOKEN in environment.")
    client.run(DISCORD_BOT_TOKEN)
