# Queue IDs for Summoner's Rift modes only
SUMMONERS_RIFT_QUEUE_IDS = {
    400,  # Normal Draft
    420,  # Ranked Solo/Duo
    430,  # Normal Blind
    440,  # Ranked Flex
}


def is_summoners_rift(match_info: dict) -> bool:
    """Check if the match was played on Summoner's Rift."""
    queue_id = match_info.get("queueId", 0)
    return queue_id in SUMMONERS_RIFT_QUEUE_IDS
