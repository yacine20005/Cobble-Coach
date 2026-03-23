# League of Legends Coach

An advanced Discord bot leveraging the Riot Games API and Google's Gemini Pro LLM to provide automated, data-driven coaching for League of Legends players. This project demonstrates proficiency in backend development, third-party API integration, data analysis, and prompt engineering.

## Project Overview

The goal of this project is to democratize access to high-level game analysis. By fetching raw match data and processing it through a Large Language Model (LLM), the bot generates personalized, actionable advice comparable to human coaching. It analyzes key performance indicators (KPIs) from a player's last 20 matches to identify patterns, strengths, and areas for improvement.

## Tech Stack & Key Skills

*   **Language:** Python 3.12+
*   **Discord Integration:** `discord.py` (Asynchronous command handling, slash commands)
*   **Data Source:** Riot Games API (MatchV5, SummonerV4, AccountV1)
*   **Artificial Intelligence:** Google Gemini 2.5 flash (via `google-genai`)
*   **Data Processing:** Pandas (Dataframes, aggregation), JSON manipulation
*   **Serialization:** TOON (Token-Oriented Object Notation) for optimized LLM context usage
*   **Environment Management:** `python-dotenv` for secure configuration

## Architecture & Workflow

The application follows a modular pipeline designed for efficiency and scalability:

1.  **User Interaction:** A user invokes the `/coach` slash command with their Riot ID and Tagline.
2.  **Data Ingestion:**
    *   Resolves the user's PUUID via the Riot Account API.
    *   Fetches the list of the last 20 match IDs via the MatchV5 API.
    *   Iteratively retrieves detailed match data (participants, timelines, challenges).
3.  **Data Processing:**
    *   Filters and extracts relevant player metrics (KDA, CS/min, Vision Score, Damage Share, Objective Control).
    *   Normalizes data into a structured format suitable for analysis.
4.  **AI Analysis:**
    *   Constructs a context-aware prompt using the aggregated match data.
    *   Sends the prompt to the Gemini model.
    *   Receives a structured critique covering mechanics, macro-play, and strategic recommendations.
5.  **Response Delivery:**
    *   Chunks the potentially long AI response to fit within Discord's message limits.
    *   Delivers the coaching report back to the user in the channel.

## Key Features

*   **Automated Match History Analysis:** Instantly processes multiple recent games to find trends.
*   **Deep Statistical Insight:** Goes beyond basic KDA to analyze:
    *   Economy (Gold/min, Itemization efficiency)
    *   Laning Phase (CS/min, XP differentials, Solo kills)
    *   Team Contribution (Kill Participation, Damage Share, Vision Control)
*   **Frame-by-Frame Deep Analysis:** Analyze a single match in extreme detail with timeline data:
    *   Position tracking for all 10 players every minute
    *   Complete event history (kills, items, objectives, wards)
    *   Gold/CS differentials throughout the game
    *   Combat stats evolution (damage, armor, attack speed, etc.)
    *   Actionable insights with precise timestamps
*   **Personalized Coaching:** The AI adapts its advice based on the specific champion pool and role played.
*   **Data Export Utility:** Includes a standalone script (`export.py`) to dump match data into CSV, JSON, and TOON formats for offline analysis or dataset creation.

## Usage

### Discord Bot Commands

*   `/coach [game_name] [tag_line]` - Analyze multiple recent games for trends and patterns
*   `/deep-coach [game_name] [tag_line] [match_index]` - Deep frame-by-frame analysis of a single game
    *   `match_index`: 0 = most recent match, 1 = second most recent, etc. (default: 0)

### Standalone Export Tool

Export match data without using the Discord bot:

```bash
# Export multiple matches overview
python export.py

# Export detailed frame-by-frame analysis of a single match
python export.py --detailed --match-index 0

# Override player credentials
python export.py --detailed --game-name "PlayerName" --tag-line "TAG" --match-index 0
```

The detailed export generates a comprehensive JSON file with:
- All 10 players' statistics and timeline data
- Frame-by-frame snapshots (every minute)
- Complete event log with timestamps
- Gold/CS differentials
- Combat stats evolution

## Installation & Setup

### Prerequisites

*   Python 3.8 or higher
*   A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
*   A Riot Games API Key ([Riot Developer Portal](https://developer.riotgames.com/))
*   A Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/lol-ai-coach.git
    cd lol-ai-coach
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Create a `.env` file in the root directory:
    ```dotenv
    DISCORD_BOT_TOKEN=your_discord_token
    RIOT_API_KEY=your_riot_key
    GEMINI_API_KEY=your_gemini_key

    # Riot ID
    GAME_NAME=YourRiotID
    TAG_LINE=YourTagLine
    TOTAL_GAMES=100
    REGION_ROUTING=europe
    GEMINI_MODEL=gemini-1.5-pro
    ```

4.  **Run the Bot:**
    ```bash
    python bot.py
    ```

## Future Improvements

*   **Visualizations:** Generate graphs for Gold/XP leads using `matplotlib` or `seaborn` and embed them in Discord responses.
*   **Database Integration:** Store user profiles and historical analysis to track improvement over time.
*   **Multi-Region Support:** Enhanced routing logic to support players from all Riot regions dynamically.
