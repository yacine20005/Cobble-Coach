from lol_coach.riot_api import fetch_match_info, fetch_match_timeline
from lol_coach.match_processing import find_player_participant, build_game_record
from lol_coach.timeline_processing import (
    extract_participant_frames,
    extract_events,
    calculate_gold_diff_timeline,
    calculate_cs_diff_timeline,
    get_participant_events,
    build_timeline_summary,
)


def map_puuid_to_participant_id(info: dict, puuid: str) -> int | None:
    """
    Map a PUUID to its participantId (1-10).
    """
    for participant in info.get("participants", []):
        if participant.get("puuid") == puuid:
            return participant.get("participantId")
    return None


def get_lane_opponent_id(info: dict, target_participant_id: int) -> int | None:
    """
    Find the lane opponent for a given participant.
    Matches by teamPosition and opposite team.
    """
    target_participant = None
    for participant in info.get("participants", []):
        if participant.get("participantId") == target_participant_id:
            target_participant = participant
            break
    
    if not target_participant:
        return None
    
    target_position = target_participant.get("teamPosition", "")
    target_team_id = target_participant.get("teamId", 0)
    
    if not target_position:
        return None
    
    for participant in info.get("participants", []):
        if (participant.get("teamPosition") == target_position and 
            participant.get("teamId") != target_team_id):
            return participant.get("participantId")
    
    return None


def build_all_participants_data(info: dict, duration: int, target_puuid: str | None = None) -> list[dict]:
    """
    Build game records for all 10 participants.
    If target_puuid is provided, marks the target player with is_target_player flag.
    """
    all_participants = []
    
    for participant in info.get("participants", []):
        participant_record = build_game_record(participant, duration)
        participant_record["participant_id"] = participant.get("participantId")
        participant_record["puuid"] = participant.get("puuid")
        participant_record["summoner_name"] = participant.get("summonerName", "")
        participant_record["riot_id_game_name"] = participant.get("riotIdGameName", "")
        participant_record["riot_id_tag_line"] = participant.get("riotIdTagline", "")
        participant_record["team_id"] = participant.get("teamId")
        participant_record["is_target_player"] = (participant.get("puuid") == target_puuid) if target_puuid else False
        all_participants.append(participant_record)
    
    return all_participants


def build_detailed_game_analysis(
    match_id: str,
    puuid: str,
    headers: dict,
    region_routing: str = "europe"
) -> dict | None:
    """
    Build a comprehensive analysis combining match info and timeline data.
    Includes all 10 players for full context.
    """
    match_info = fetch_match_info(match_id, headers, region_routing)
    if not match_info:
        print(f"  Failed to fetch match info for {match_id}")
        return None
    
    timeline_data = fetch_match_timeline(match_id, headers, region_routing)
    if not timeline_data:
        print(f"  Failed to fetch timeline for {match_id}")
        return None
    
    duration = match_info.get("gameDuration", 0)
    game_mode = match_info.get("gameMode", "")
    game_type = match_info.get("gameType", "")
    map_id = match_info.get("mapId", 0)
    
    target_participant = find_player_participant(match_info, puuid)
    if not target_participant:
        print(f"  Target player not found in match {match_id}")
        return None
    
    target_participant_id = target_participant.get("participantId")
    
    all_participants = build_all_participants_data(match_info, duration, puuid)
    
    participant_frames = extract_participant_frames(timeline_data)
    all_events = extract_events(timeline_data)
    timeline_summary = build_timeline_summary(timeline_data)
    
    target_events = get_participant_events(all_events, target_participant_id)
    
    opponent_id = get_lane_opponent_id(match_info, target_participant_id)
    gold_diff = []
    cs_diff = []
    
    if opponent_id:
        gold_diff = calculate_gold_diff_timeline(participant_frames, target_participant_id, opponent_id)
        cs_diff = calculate_cs_diff_timeline(participant_frames, target_participant_id, opponent_id)
    
    objective_events = [e for e in all_events if e["event_type"] in [
        "ELITE_MONSTER_KILL", "BUILDING_KILL", "TURRET_PLATE_DESTROYED"
    ]]
    
    target_participant_full_stats = None
    for p in all_participants:
        if p["participant_id"] == target_participant_id:
            target_participant_full_stats = p
            break
    
    return {
        "match_id": match_id,
        "game_metadata": {
            "game_mode": game_mode,
            "game_type": game_type,
            "map_id": map_id,
            "duration_seconds": duration,
            "duration_minutes": round(duration / 60, 2),
        },
        "target_player": {
            "puuid": puuid,
            "participant_id": target_participant_id,
            "summoner_name": target_participant.get("summonerName", ""),
            "riot_id": f"{target_participant.get('riotIdGameName', '')}#{target_participant.get('riotIdTagline', '')}",
            "champion": target_participant.get("championName", ""),
            "team_id": target_participant.get("teamId"),
            "win": target_participant.get("win", False),
            "lane_opponent_id": opponent_id,
            "full_game_stats": target_participant_full_stats,
        },
        "target_player_timeline": {
            "frames": participant_frames.get(target_participant_id, []),
            "events": target_events,
            "gold_diff_vs_opponent": gold_diff,
            "cs_diff_vs_opponent": cs_diff,
        },
        "all_participants": all_participants,
        "all_participants_timeline": {
            "frames": participant_frames,
            "all_events": all_events,
            "objective_events": objective_events,
        },
        "timeline_summary": timeline_summary,
    }
