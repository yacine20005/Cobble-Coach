from lol_coach.config import get_int_env_var, get_optional_env_var, get_required_env_var
from lol_coach.export_service import (
    collect_games_data,
    export_tabular_files,
    export_toon_file,
)
from lol_coach.riot_api import build_headers, get_match_ids, get_puuid


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


def main():
    run_export(GAME_NAME, TAG_LINE, TOTAL_GAMES)


if __name__ == "__main__":
    main()
