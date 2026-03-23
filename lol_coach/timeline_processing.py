def extract_participant_frames(timeline_data: dict) -> dict:
    """
    Extract participant frame data from timeline.
    Returns a dict mapping participantId to list of frame snapshots.
    """
    if not timeline_data or "info" not in timeline_data:
        return {}
    
    info = timeline_data["info"]
    frames = info.get("frames", [])
    
    participant_timeline = {}
    
    for frame_idx, frame in enumerate(frames):
        timestamp = frame.get("timestamp", 0)
        participant_frames = frame.get("participantFrames", {})
        
        for participant_id_str, participant_data in participant_frames.items():
            participant_id = int(participant_id_str)
            
            if participant_id not in participant_timeline:
                participant_timeline[participant_id] = []
            
            frame_snapshot = {
                "frame_index": frame_idx,
                "timestamp_ms": timestamp,
                "timestamp_min": round(timestamp / 60000, 2),
                "current_gold": participant_data.get("currentGold", 0),
                "total_gold": participant_data.get("totalGold", 0),
                "level": participant_data.get("level", 0),
                "xp": participant_data.get("xp", 0),
                "minions_killed": participant_data.get("minionsKilled", 0),
                "jungle_minions_killed": participant_data.get("jungleMinionsKilled", 0),
                "time_enemy_spent_controlled": participant_data.get("timeEnemySpentControlled", 0),
                "position_x": participant_data.get("position", {}).get("x", 0),
                "position_y": participant_data.get("position", {}).get("y", 0),
            }
            
            champion_stats = participant_data.get("championStats", {})
            if champion_stats:
                frame_snapshot.update({
                    "ability_power": champion_stats.get("abilityPower", 0),
                    "armor": champion_stats.get("armor", 0),
                    "armor_pen": champion_stats.get("armorPen", 0),
                    "armor_pen_percent": champion_stats.get("armorPenPercent", 0),
                    "attack_damage": champion_stats.get("attackDamage", 0),
                    "attack_speed": champion_stats.get("attackSpeed", 0),
                    "bonus_armor_pen_percent": champion_stats.get("bonusArmorPenPercent", 0),
                    "bonus_magic_pen_percent": champion_stats.get("bonusMagicPenPercent", 0),
                    "cc_reduction": champion_stats.get("ccReduction", 0),
                    "cooldown_reduction": champion_stats.get("cooldownReduction", 0),
                    "health": champion_stats.get("health", 0),
                    "health_max": champion_stats.get("healthMax", 0),
                    "health_regen": champion_stats.get("healthRegen", 0),
                    "lifesteal": champion_stats.get("lifesteal", 0),
                    "magic_pen": champion_stats.get("magicPen", 0),
                    "magic_pen_percent": champion_stats.get("magicPenPercent", 0),
                    "magic_resist": champion_stats.get("magicResist", 0),
                    "movement_speed": champion_stats.get("movementSpeed", 0),
                    "omnivamp": champion_stats.get("omnivamp", 0),
                    "physical_vamp": champion_stats.get("physicalVamp", 0),
                    "power": champion_stats.get("power", 0),
                    "power_max": champion_stats.get("powerMax", 0),
                    "power_regen": champion_stats.get("powerRegen", 0),
                    "spell_vamp": champion_stats.get("spellVamp", 0),
                })
            
            damage_stats = participant_data.get("damageStats", {})
            if damage_stats:
                frame_snapshot.update({
                    "magic_damage_done": damage_stats.get("magicDamageDone", 0),
                    "magic_damage_done_to_champions": damage_stats.get("magicDamageDoneToChampions", 0),
                    "magic_damage_taken": damage_stats.get("magicDamageTaken", 0),
                    "physical_damage_done": damage_stats.get("physicalDamageDone", 0),
                    "physical_damage_done_to_champions": damage_stats.get("physicalDamageDoneToChampions", 0),
                    "physical_damage_taken": damage_stats.get("physicalDamageTaken", 0),
                    "total_damage_done": damage_stats.get("totalDamageDone", 0),
                    "total_damage_done_to_champions": damage_stats.get("totalDamageDoneToChampions", 0),
                    "total_damage_taken": damage_stats.get("totalDamageTaken", 0),
                    "true_damage_done": damage_stats.get("trueDamageDone", 0),
                    "true_damage_done_to_champions": damage_stats.get("trueDamageDoneToChampions", 0),
                    "true_damage_taken": damage_stats.get("trueDamageTaken", 0),
                })
            
            participant_timeline[participant_id].append(frame_snapshot)
    
    return participant_timeline


def extract_events(timeline_data: dict) -> list[dict]:
    """
    Extract all events from timeline frames.
    Returns a flat list of all events with timestamps.
    """
    if not timeline_data or "info" not in timeline_data:
        return []
    
    info = timeline_data["info"]
    frames = info.get("frames", [])
    
    all_events = []
    
    for frame_idx, frame in enumerate(frames):
        timestamp = frame.get("timestamp", 0)
        events = frame.get("events", [])
        
        for event in events:
            event_type = event.get("type", "UNKNOWN")
            
            processed_event = {
                "frame_index": frame_idx,
                "timestamp_ms": timestamp,
                "timestamp_min": round(timestamp / 60000, 2),
                "event_type": event_type,
                "real_timestamp_ms": event.get("realTimestamp", event.get("timestamp", timestamp)),
            }
            
            if event_type == "CHAMPION_KILL":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "victim_id": event.get("victimId", 0),
                    "assisting_participant_ids": event.get("assistingParticipantIds", []),
                    "position_x": event.get("position", {}).get("x", 0),
                    "position_y": event.get("position", {}).get("y", 0),
                    "bounty": event.get("bounty", 0),
                    "shutdown_bounty": event.get("shutdownBounty", 0),
                    "kill_streak_length": event.get("killStreakLength", 0),
                    "victim_damage_dealt": event.get("victimDamageDealt", []),
                    "victim_damage_received": event.get("victimDamageReceived", []),
                })
            
            elif event_type == "BUILDING_KILL":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "team_id": event.get("teamId", 0),
                    "building_type": event.get("buildingType", ""),
                    "lane_type": event.get("laneType", ""),
                    "tower_type": event.get("towerType", ""),
                    "position_x": event.get("position", {}).get("x", 0),
                    "position_y": event.get("position", {}).get("y", 0),
                    "assisting_participant_ids": event.get("assistingParticipantIds", []),
                })
            
            elif event_type == "ELITE_MONSTER_KILL":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "killer_team_id": event.get("killerTeamId", 0),
                    "monster_type": event.get("monsterType", ""),
                    "monster_sub_type": event.get("monsterSubType", ""),
                    "position_x": event.get("position", {}).get("x", 0),
                    "position_y": event.get("position", {}).get("y", 0),
                    "assisting_participant_ids": event.get("assistingParticipantIds", []),
                })
            
            elif event_type == "ITEM_PURCHASED":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "item_id": event.get("itemId", 0),
                })
            
            elif event_type == "ITEM_SOLD":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "item_id": event.get("itemId", 0),
                })
            
            elif event_type == "ITEM_DESTROYED":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "item_id": event.get("itemId", 0),
                })
            
            elif event_type == "ITEM_UNDO":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "before_id": event.get("beforeId", 0),
                    "after_id": event.get("afterId", 0),
                })
            
            elif event_type == "WARD_PLACED":
                processed_event.update({
                    "creator_id": event.get("creatorId", 0),
                    "ward_type": event.get("wardType", ""),
                })
            
            elif event_type == "WARD_KILL":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "ward_type": event.get("wardType", ""),
                })
            
            elif event_type == "LEVEL_UP":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "level": event.get("level", 0),
                })
            
            elif event_type == "SKILL_LEVEL_UP":
                processed_event.update({
                    "participant_id": event.get("participantId", 0),
                    "skill_slot": event.get("skillSlot", 0),
                    "level_up_type": event.get("levelUpType", ""),
                })
            
            elif event_type == "GAME_END":
                processed_event.update({
                    "winning_team": event.get("winningTeam", 0),
                    "game_id": event.get("gameId", 0),
                })
            
            elif event_type == "CHAMPION_SPECIAL_KILL":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "kill_type": event.get("killType", ""),
                    "multi_kill_length": event.get("multiKillLength", 0),
                })
            
            elif event_type == "TURRET_PLATE_DESTROYED":
                processed_event.update({
                    "killer_id": event.get("killerId", 0),
                    "team_id": event.get("teamId", 0),
                    "lane_type": event.get("laneType", ""),
                    "position_x": event.get("position", {}).get("x", 0),
                    "position_y": event.get("position", {}).get("y", 0),
                })
            
            all_events.append(processed_event)
    
    return all_events


def calculate_gold_diff_timeline(participant_timeline: dict, target_participant_id: int, opponent_participant_id: int) -> list[dict]:
    """
    Calculate gold difference between two participants across all frames.
    """
    if target_participant_id not in participant_timeline or opponent_participant_id not in participant_timeline:
        return []
    
    target_frames = participant_timeline[target_participant_id]
    opponent_frames = participant_timeline[opponent_participant_id]
    
    gold_diff_timeline = []
    
    for i, target_frame in enumerate(target_frames):
        if i < len(opponent_frames):
            opponent_frame = opponent_frames[i]
            gold_diff = target_frame["total_gold"] - opponent_frame["total_gold"]
            
            gold_diff_timeline.append({
                "timestamp_ms": target_frame["timestamp_ms"],
                "timestamp_min": target_frame["timestamp_min"],
                "gold_diff": gold_diff,
                "target_gold": target_frame["total_gold"],
                "opponent_gold": opponent_frame["total_gold"],
            })
    
    return gold_diff_timeline


def calculate_cs_diff_timeline(participant_timeline: dict, target_participant_id: int, opponent_participant_id: int) -> list[dict]:
    """
    Calculate CS (minions + jungle) difference between two participants across all frames.
    """
    if target_participant_id not in participant_timeline or opponent_participant_id not in participant_timeline:
        return []
    
    target_frames = participant_timeline[target_participant_id]
    opponent_frames = participant_timeline[opponent_participant_id]
    
    cs_diff_timeline = []
    
    for i, target_frame in enumerate(target_frames):
        if i < len(opponent_frames):
            opponent_frame = opponent_frames[i]
            target_cs = target_frame["minions_killed"] + target_frame["jungle_minions_killed"]
            opponent_cs = opponent_frame["minions_killed"] + opponent_frame["jungle_minions_killed"]
            cs_diff = target_cs - opponent_cs
            
            cs_diff_timeline.append({
                "timestamp_ms": target_frame["timestamp_ms"],
                "timestamp_min": target_frame["timestamp_min"],
                "cs_diff": cs_diff,
                "target_cs": target_cs,
                "opponent_cs": opponent_cs,
            })
    
    return cs_diff_timeline


def get_participant_events(events: list[dict], participant_id: int) -> dict:
    """
    Filter events relevant to a specific participant and categorize them.
    """
    participant_events = {
        "kills": [],
        "deaths": [],
        "assists": [],
        "items_purchased": [],
        "items_sold": [],
        "wards_placed": [],
        "wards_killed": [],
        "level_ups": [],
        "skill_level_ups": [],
    }
    
    for event in events:
        event_type = event["event_type"]
        
        if event_type == "CHAMPION_KILL":
            if event.get("killer_id") == participant_id:
                participant_events["kills"].append(event)
            if event.get("victim_id") == participant_id:
                participant_events["deaths"].append(event)
            if participant_id in event.get("assisting_participant_ids", []):
                participant_events["assists"].append(event)
        
        elif event_type == "ITEM_PURCHASED" and event.get("participant_id") == participant_id:
            participant_events["items_purchased"].append(event)
        
        elif event_type == "ITEM_SOLD" and event.get("participant_id") == participant_id:
            participant_events["items_sold"].append(event)
        
        elif event_type == "WARD_PLACED" and event.get("creator_id") == participant_id:
            participant_events["wards_placed"].append(event)
        
        elif event_type == "WARD_KILL" and event.get("killer_id") == participant_id:
            participant_events["wards_killed"].append(event)
        
        elif event_type == "LEVEL_UP" and event.get("participant_id") == participant_id:
            participant_events["level_ups"].append(event)
        
        elif event_type == "SKILL_LEVEL_UP" and event.get("participant_id") == participant_id:
            participant_events["skill_level_ups"].append(event)
    
    return participant_events


def build_timeline_summary(timeline_data: dict) -> dict:
    """
    Build a comprehensive summary of the timeline data.
    Returns metadata and high-level statistics.
    """
    if not timeline_data or "info" not in timeline_data:
        return {}
    
    info = timeline_data["info"]
    frames = info.get("frames", [])
    
    return {
        "frame_interval_ms": info.get("frameInterval", 60000),
        "total_frames": len(frames),
        "game_duration_frames": len(frames) - 1 if frames else 0,
    }
