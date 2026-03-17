import os
import json
import time
import asyncio
import requests
import discord
from discord import app_commands
from dotenv import load_dotenv
import google.genai as genai

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

HEADERS = {"X-Riot-Token": RIOT_API_KEY}


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


def get_account_puuid(game_name: str, tag_line: str) -> str:
    url = (
        f"https://{REGION_ROUTING}.api.riotgames.com/riot/account/v1/accounts"
        f"/by-riot-id/{game_name}/{tag_line}"
    )
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["puuid"]


def get_match_ids(puuid: str, total_games: int = 50) -> list[str]:
    match_ids: list[str] = []
    start = 0

    while len(match_ids) < total_games:
        url = (
            f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches"
            f"/by-puuid/{puuid}/ids?start={start}&count=100"
        )
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        match_ids.extend(batch)
        start += 100
        time.sleep(1.2)

    return match_ids[:total_games]


def fetch_match(match_id: str, retries: int = 3) -> dict | None:
    url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 429:
                time.sleep(2 + attempt * 2)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            time.sleep(2 + attempt * 2)
            continue
        except requests.exceptions.RequestException:
            if attempt == retries - 1:
                return None
            time.sleep(2 + attempt * 2)
            continue
    return None


def extract_player_data(info: dict, puuid: str) -> dict | None:
    duration = info.get("gameDuration", 0)
    for p in info.get("participants", []):
        if p.get("puuid") != puuid:
            continue

        kda = (p.get("kills", 0) + p.get("assists", 0)) / max(1, p.get("deaths", 0))
        cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
        cs_per_min = cs / (duration / 60) if duration else 0

        items = [p.get(f"item{i}", 0) for i in range(7)]
        challenges = p.get("challenges", {})

        return {
            "champion": p.get("championName", ""),
            "role": p.get("role", ""),
            "lane": p.get("lane", ""),
            "team_position": p.get("teamPosition", ""),
            "individual_position": p.get("individualPosition", ""),
            "win": p.get("win", False),
            "kills": p.get("kills", 0),
            "deaths": p.get("deaths", 0),
            "assists": p.get("assists", 0),
            "kda": round(kda, 2),
            "cs": cs,
            "cs_per_min": round(cs_per_min, 2),
            "gold": p.get("goldEarned", 0),
            "gold_spent": p.get("goldSpent", 0),
            "damage_dealt": p.get("totalDamageDealtToChampions", 0),
            "damage_dealt_to_objectives": p.get("damageDealtToObjectives", 0),
            "damage_dealt_to_buildings": p.get("damageDealtToBuildings", 0),
            "physical_damage_dealt": p.get("physicalDamageDealt", 0),
            "magic_damage_dealt": p.get("magicDamageDealt", 0),
            "true_damage_dealt": p.get("trueDamageDealt", 0),
            "physical_damage_to_champs": p.get("physicalDamageDealtToChampions", 0),
            "magic_damage_to_champs": p.get("magicDamageDealtToChampions", 0),
            "true_damage_to_champs": p.get("trueDamageDealtToChampions", 0),
            "damage_taken": p.get("totalDamageTaken", 0),
            "physical_damage_taken": p.get("physicalDamageTaken", 0),
            "magic_damage_taken": p.get("magicDamageTaken", 0),
            "true_damage_taken": p.get("trueDamageTaken", 0),
            "damage_self_mitigated": p.get("damageSelfMitigated", 0),
            "total_heal": p.get("totalHeal", 0),
            "total_heal_on_teammates": p.get("totalHealsOnTeammates", 0),
            "damage_shielded_on_teammates": p.get("totalDamageShieldedOnTeammates", 0),
            "total_cc_dealt": p.get("timeCCingOthers", 0),
            "total_time_cc_dealt": p.get("totalTimeCCDealt", 0),
            "vision_score": p.get("visionScore", 0),
            "wards_placed": p.get("wardsPlaced", 0),
            "wards_killed": p.get("wardsKilled", 0),
            "sight_wards_bought": p.get("sightWardsBoughtInGame", 0),
            "vision_wards_bought": p.get("visionWardsBoughtInGame", 0),
            "detector_wards_placed": p.get("detectorWardsPlaced", 0),
            "pentakills": p.get("pentaKills", 0),
            "quadrakills": p.get("quadraKills", 0),
            "triplekills": p.get("tripleKills", 0),
            "doublekills": p.get("doubleKills", 0),
            "multikills": p.get("largestMultiKill", 0),
            "dragon_kills": p.get("dragonKills", 0),
            "baron_kills": p.get("baronKills", 0),
            "turret_kills": p.get("turretKills", 0),
            "turret_takedowns": p.get("turretTakedowns", 0),
            "turrets_lost": p.get("turretsLost", 0),
            "inhibitor_kills": p.get("inhibitorKills", 0),
            "inhibitor_takedowns": p.get("inhibitorTakedowns", 0),
            "inhibitors_lost": p.get("inhibitorsLost", 0),
            "nexus_kills": p.get("nexusKills", 0),
            "nexus_takedowns": p.get("nexusTakedowns", 0),
            "total_ally_jungle_minions": p.get("totalAllyJungleMinionsKilled", 0),
            "total_enemy_jungle_minions": p.get("totalEnemyJungleMinionsKilled", 0),
            "true_mitigated_damage": p.get("damageSelfMitigated", 0),
            "longest_time_alive": p.get("longestTimeSpentLiving", 0),
            "total_time_dead": p.get("totalTimeSpentDead", 0),
            "killing_sprees": p.get("killingSprees", 0),
            "largest_killing_spree": p.get("largestKillingSpree", 0),
            "first_blood_kill": p.get("firstBloodKill", False),
            "first_blood_assist": p.get("firstBloodAssist", False),
            "first_tower_kill": p.get("firstTowerKill", False),
            "first_tower_assist": p.get("firstTowerAssist", False),
            "champ_level": p.get("champLevel", 0),
            "champ_experience": p.get("champExperience", 0),
            "summoner1_id": p.get("summoner1Id", 0),
            "summoner2_id": p.get("summoner2Id", 0),
            "summoner1_casts": p.get("summoner1Casts", 0),
            "summoner2_casts": p.get("summoner2Casts", 0),
            "spell1_casts": p.get("spell1Casts", 0),
            "spell2_casts": p.get("spell2Casts", 0),
            "spell3_casts": p.get("spell3Casts", 0),
            "spell4_casts": p.get("spell4Casts", 0),
            "item0": items[0],
            "item1": items[1],
            "item2": items[2],
            "item3": items[3],
            "item4": items[4],
            "item5": items[5],
            "item6": items[6],
            "items_purchased": p.get("itemsPurchased", 0),
            "consumables_purchased": p.get("consumablesPurchased", 0),
            "bounce_level": p.get("bountyLevel", 0),
            "unrealized_kills": p.get("unrealKills", 0),
            "time_played": p.get("timePlayed", 0),
            "game_ended_in_surrender": p.get("gameEndedInSurrender", False),
            "game_ended_in_early_surrender": p.get("gameEndedInEarlySurrender", False),
            "team_early_surrendered": p.get("teamEarlySurrendered", False),
            "gold_per_minute": round(challenges.get("goldPerMinute", 0), 2),
            "damage_per_minute": round(challenges.get("damagePerMinute", 0), 2),
            "vision_score_per_minute": round(challenges.get("visionScorePerMinute", 0), 2),
            "kill_participation": round(challenges.get("killParticipation", 0), 3),
            "kda_challenge": round(challenges.get("kda", 0), 2),
            "largest_critical_strike": p.get("largestCriticalStrike", 0),
            "damage_taken_on_team_percentage": round(
                challenges.get("damageTakenOnTeamPercentage", 0), 3
            ),
            "max_level_lead_lane_opponent": challenges.get("maxLevelLeadLaneOpponent", 0),
            "max_cs_advantage_on_lane_opponent": round(
                challenges.get("maxCsAdvantageOnLaneOpponent", 0), 2
            ),
            "takedowns": challenges.get("takedowns", 0),
            "takedowns_first_25_minutes": challenges.get("takedownsFirst25Minutes", 0),
            "deaths_by_enemy_champs": challenges.get("deathsByEnemyChamps", 0),
            "enemy_champ_immobilizations": challenges.get("enemyChampionImmobilizations", 0),
            "solo_kills": challenges.get("soloKills", 0),
            "outnumbered_kills": challenges.get("outnumberedKills", 0),
            "game_duration": duration,
        }

    return None


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
        puuid = await asyncio.to_thread(get_account_puuid, game_name, tag_line)
        match_ids = await asyncio.to_thread(get_match_ids, puuid, TOTAL_GAMES)
    except Exception as e:
        await interaction.followup.send(f"Failed to fetch match list: {e}")
        return

    games_data: list[dict] = []
    for match_id in match_ids:
        try:
            match_data = await asyncio.to_thread(fetch_match, match_id)
        except Exception:
            match_data = None
        if not match_data or "info" not in match_data:
            continue
        player_data = extract_player_data(match_data["info"], puuid)
        if player_data:
            games_data.append(player_data)
        await asyncio.sleep(1.5)

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
