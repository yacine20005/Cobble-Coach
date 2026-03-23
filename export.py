import json
import argparse
from lol_coach.config import get_int_env_var, get_optional_env_var, get_required_env_var
from lol_coach.export_service import (
    collect_games_data,
    export_tabular_files,
    export_toon_file,
)
from lol_coach.riot_api import build_headers, get_match_ids, get_puuid
from lol_coach.detailed_analysis import build_detailed_game_analysis


API_KEY = get_required_env_var("RIOT_API_KEY")
GAME_NAME = get_required_env_var("GAME_NAME")
TAG_LINE = get_required_env_var("TAG_LINE")
TOTAL_GAMES = get_int_env_var("TOTAL_GAMES", 20)
REGION_ROUTING = get_optional_env_var("REGION_ROUTING", "europe")


def run_export(game_name, tag_line, total_games):
    headers = build_headers(API_KEY)

    puuid = get_puuid(game_name, tag_line, headers, region_routing=REGION_ROUTING)
    print(f"PUUID for {game_name}#{tag_line}: {puuid}")

    match_ids = get_match_ids(
        puuid,
        headers,
        total_games=total_games,
        region_routing=REGION_ROUTING,
    )
    print(f"Found {len(match_ids)} recent matches for {game_name}#{tag_line}.")

    games_data = collect_games_data(
        match_ids,
        puuid,
        headers,
        region_routing=REGION_ROUTING,
        target_games=total_games,
    )
    export_tabular_files(games_data, game_name, tag_line)
    export_toon_file(games_data, game_name, tag_line)

    print(f"Export completed for {game_name}#{tag_line}. ({len(games_data)} games exported)")


def run_detailed_export(game_name, tag_line, match_index=0):
    headers = build_headers(API_KEY)

    puuid = get_puuid(game_name, tag_line, headers, region_routing=REGION_ROUTING)
    print(f"PUUID for {game_name}#{tag_line}: {puuid}")

    match_ids = get_match_ids(
        puuid,
        headers,
        total_games=max(20, match_index + 5),
        region_routing=REGION_ROUTING,
    )
    
    if match_index >= len(match_ids):
        print(f"Error: match_index {match_index} out of range. Only {len(match_ids)} matches found.")
        return
    
    target_match_id = match_ids[match_index]
    print(f"Analyzing match {target_match_id} (index {match_index})...")

    detailed_analysis = build_detailed_game_analysis(
        target_match_id,
        puuid,
        headers,
        REGION_ROUTING
    )
    
    if not detailed_analysis:
        print("Failed to build detailed analysis.")
        return
    
    filename = f"{game_name}_{tag_line}_detailed_match_{match_index}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(detailed_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"Detailed analysis exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Export LoL match data")
    parser.add_argument("--detailed", action="store_true", help="Export detailed frame-by-frame analysis for a single match")
    parser.add_argument("--match-index", type=int, default=0, help="Match index for detailed export (0 = most recent)")
    parser.add_argument("--game-name", type=str, help="Override game name from env")
    parser.add_argument("--tag-line", type=str, help="Override tag line from env")
    parser.add_argument("--total-games", type=int, help="Override total games from env")
    
    args = parser.parse_args()
    
    game_name = args.game_name or GAME_NAME
    tag_line = args.tag_line or TAG_LINE
    total_games = args.total_games or TOTAL_GAMES
    
    if args.detailed:
        run_detailed_export(game_name, tag_line, args.match_index)
    else:
        run_export(game_name, tag_line, total_games)


if __name__ == "__main__":
    main()
