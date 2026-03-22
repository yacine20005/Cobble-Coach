import time

import requests


def build_headers(api_key: str) -> dict:
    """Return Riot API authentication headers."""
    return {"X-Riot-Token": api_key}


def get_puuid(game_name: str, tag_line: str, headers: dict, region_routing: str = "europe") -> str:
    """Resolve a Riot ID (game_name#tag_line) to a PUUID via the Account API."""
    url = (
        f"https://{region_routing}.api.riotgames.com/riot/account/v1/accounts"
        f"/by-riot-id/{game_name}/{tag_line}"
    )
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()["puuid"]
    raise requests.exceptions.RequestException(
        f"Error fetching PUUID: {response.status_code} - {response.text}"
    )


def get_match_ids(
    puuid: str,
    headers: dict,
    total_games: int = 300,
    batch_size: int = 100,
    region_routing: str = "europe",
    sleep_seconds: float = 1.0,
) -> list[str]:
    """
    Fetch match IDs for the given PUUID in paginated batches.
    Fetches 2x total_games to account for filtering out non-Summoner's Rift games.
    """
    match_ids: list[str] = []
    start = 0
    # Fetch extra matches to ensure we have enough after filtering
    target = total_games * 2

    while len(match_ids) < target:
        url = (
            f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches"
            f"/by-puuid/{puuid}/ids?start={start}&count={batch_size}"
        )
        response = requests.get(url, headers=headers, timeout=10)
        batch = response.json()

        if not batch:
            break

        match_ids.extend(batch)
        start += batch_size
        time.sleep(sleep_seconds)

    return match_ids[:target]


def fetch_match_info(match_id: str, headers: dict, region_routing: str = "europe") -> dict | None:
    """Fetch the 'info' block of a single match, or return None on failure."""
    url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        info = response.json().get("info")
        if info is None:
            print(f"  Warning: No 'info' in match data for {match_id}")
        return info
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching match {match_id}: {e}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        print(f"  Unexpected error processing {match_id}: {e}")
        return None
