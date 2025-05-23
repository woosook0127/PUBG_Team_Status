from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Pydantic models will be in main.py, but for clarity in function signature:
# class TeammatePerformanceStat(BaseModel):
#     teammate_account_id: str
#     teammate_name: Optional[str] = None # Future enhancement
#     matches_played_together: int
#     avg_kills: float
#     avg_damage_dealt: float
#     avg_survival_time_seconds: float
#     avg_match_rank: float # Lower is better
#     avg_assists: float


def calculate_team_performance_from_matches(
    main_player_account_id: str,
    team_member_account_ids: List[str],
    processed_match_details_list: List[Dict[str, Any]],
    requested_season_id: str # For filtering matches by the specific season of interest
    # platform_shard is not directly needed here if matches are pre-filtered or season is in match data
) -> List[Dict[str, Any]]: # Returns a list of dicts that can be cast to TeammatePerformanceStat
    """
    Calculates performance statistics for each teammate when playing with the main player,
    using pre-fetched and processed match details relevant to the team identification.

    Args:
        main_player_account_id: The account ID of the main player.
        team_member_account_ids: List of account IDs of the identified team members.
        processed_match_details_list: List of match detail objects already fetched by team_analyzer.
        requested_season_id: The specific season ID to filter matches for performance analysis.

    Returns:
        A list of dictionaries, each representing TeammatePerformanceStat.
    """
    
    all_teammates_performance: List[Dict[str, Any]] = []

    # Iterate through each teammate (excluding the main player themselves if they are in the list)
    for teammate_id in team_member_account_ids:
        if teammate_id == main_player_account_id:
            continue

        # Store aggregated stats for this teammate
        aggregated_stats = {
            "kills": 0,
            "damage_dealt": 0,
            "survival_time_seconds": 0,
            "match_rank": 0, # Sum of ranks
            "assists": 0,
            "matches_played_together": 0
        }

        for match_details in processed_match_details_list:
            # 1. Verify if the match belongs to the requested_season_id
            # The match object structure for season ID needs to be confirmed.
            # Common paths: data.attributes.seasonState (maps to a season), or a direct seasonId field.
            # For now, let's assume a hypothetical `match_details['data']['attributes']['customSeason']` or similar.
            # This needs to be robust. If `identify_player_team` uses general match history,
            # this season check is crucial. If it uses season-specific history, it's less critical but good for safety.
            
            match_season_data = match_details.get("data", {}).get("attributes", {})
            # Example check (needs to be adapted to actual PUBG API response structure for match season):
            # PUBG API often provides `data.attributes.seasonState` (e.g., "progress", "closed")
            # and the actual season ID might be part of a different system or implied by the API endpoint used
            # to get match history initially.
            # For player lifetime stats per season: /players/{id}/seasons/{seasonId}
            # For match details: /matches/{matchId} - the match object itself contains `data.attributes.seasonState`.
            # It *doesn't* directly contain the full season ID like "division.bro.official.steam-2023-07".
            # This implies that `identify_player_team` (if it uses general match history) might fetch matches from various seasons.
            # The `requested_season_id` parameter is thus important here.
            #
            # A practical approach: The `identify_player_team` likely analyzes recent matches.
            # If the team performance is requested for a *specific* season, we must filter these recent matches.
            # However, the match object itself doesn't typically give the *exact* filterable season ID string.
            # This is a known challenge with the PUBG API for this kind of granular cross-referencing.
            #
            # Workaround/Assumption: For this implementation, we'll assume that if `identify_player_team`
            # was called in a context where a season was already specified (e.g., if it used a
            # season-specific match history endpoint if one existed), then `processed_match_details_list`
            # is already relevant to *a* season, but maybe not *the* specific `requested_season_id`.
            # The most robust solution would be for `identify_player_team` to also return the season for each match if possible,
            # or for `pubg_api` to have a way to get season-specific match history directly.
            #
            # Given the current `pubg_api.get_player_match_history_ids` is generic, we cannot reliably filter by `requested_season_id`
            # from the `match_details` object alone without more information or assumptions.
            #
            # Simplification for now: We will process all matches in `processed_match_details_list`
            # and assume they are relevant to the context (e.g. "recent matches").
            # The "requested_season_id" parameter will be IGNORED in this simplified stat calculation logic
            # due to the difficulty of mapping match objects to specific season ID strings reliably.
    # This is a limitation to be documented. The `requested_season_id` is passed but using it to filter
    # generic match objects is unreliable. Stats will be for the "recent matches where team played together".
            #
            # print(f"DEBUG: Match season data: {match_season_data.get('seasonState')}, type of game: {match_season_data.get('gameMode')}")
            # if match_details.get("data",{}).get("attributes",{}).get("seasonId") != requested_season_id:
    #     continue

            participants_data = [item for item in match_details.get("included", []) if item["type"] == "participant"]
            rosters_data = [item for item in match_details.get("included", []) if item["type"] == "roster"]

            main_player_participant_id: Optional[str] = None
            teammate_participant_id: Optional[str] = None
            
            # Find participant IDs for main player and teammate
            for p_data in participants_data:
                player_id_in_stats = p_data.get("attributes", {}).get("stats", {}).get("playerId")
                if player_id_in_stats == main_player_account_id:
                    main_player_participant_id = p_data["id"]
                elif player_id_in_stats == teammate_id:
                    teammate_participant_id = p_data["id"]
                if main_player_participant_id and teammate_participant_id:
                    break
            
            if not (main_player_participant_id and teammate_participant_id):
                # Either main player or teammate not found in this match's participants (should not happen if logic is correct in analyzer)
                continue

            # Check if they were on the same roster (team)
            on_same_team = False
            teammate_stats_for_match: Optional[Dict[str, Any]] = None

            for roster_data in rosters_data:
                roster_participant_ids_set = {p["id"] for p in roster_data.get("relationships", {}).get("participants", {}).get("data", [])}
                if main_player_participant_id in roster_participant_ids_set and \
                   teammate_participant_id in roster_participant_ids_set:
                    on_same_team = True
                    # Find the teammate's participant object to extract stats
                    for p_data in participants_data:
                        if p_data["id"] == teammate_participant_id:
                            teammate_stats_for_match = p_data.get("attributes", {}).get("stats", {})
                            break
                    break # Found the roster and teammate stats

            if on_same_team and teammate_stats_for_match:
                aggregated_stats["matches_played_together"] += 1
                aggregated_stats["kills"] += teammate_stats_for_match.get("kills", 0)
                aggregated_stats["damage_dealt"] += teammate_stats_for_match.get("damageDealt", 0.0)
                aggregated_stats["survival_time_seconds"] += teammate_stats_for_match.get("timeSurvived", 0.0)
                aggregated_stats["assists"] += teammate_stats_for_match.get("assists", 0)
                
                # Match Rank (placement of their squad)
                # This is usually on the roster object, not participant stats directly.
                # Let's find the roster they were on again to get its rank.
                # (This is slightly inefficient, could be optimized by storing roster_rank earlier)
                for roster_data_for_rank in rosters_data: # Re-iterate to find their specific roster
                     roster_p_ids_set = {p["id"] for p in roster_data_for_rank.get("relationships", {}).get("participants", {}).get("data", [])}
                     if main_player_participant_id in roster_p_ids_set and teammate_participant_id in roster_p_ids_set:
                         # This is their roster. Get its rank.
                         # The rank is usually in roster_data.attributes.stats.rank or roster_data.attributes.rank
                         rank = roster_data_for_rank.get("attributes", {}).get("stats", {}).get("rank")
                         if rank is None: # Fallback, some API versions might have it directly
                            rank = roster_data_for_rank.get("attributes", {}).get("rank", 0) # Default to 0 if not found
                         aggregated_stats["match_rank"] += rank
                         break


        # Calculate averages for this teammate
        if aggregated_stats["matches_played_together"] > 0:
            num_matches = aggregated_stats["matches_played_together"]
            avg_kills = aggregated_stats["kills"] / num_matches
            avg_damage = aggregated_stats["damage_dealt"] / num_matches
            avg_survival = aggregated_stats["survival_time_seconds"] / num_matches
            avg_assists = aggregated_stats["assists"] / num_matches
            avg_rank = aggregated_stats["match_rank"] / num_matches
            
            all_teammates_performance.append({
                "teammate_account_id": teammate_id,
                "teammate_name": None, # Placeholder for future name resolution
                "matches_played_together": num_matches,
                "avg_kills": round(avg_kills, 2),
                "avg_damage_dealt": round(avg_damage, 2),
                "avg_survival_time_seconds": round(avg_survival, 2),
                "avg_match_rank": round(avg_rank, 2),
                "avg_assists": round(avg_assists, 2)
            })
        else:
            # Teammate was identified but no common matches found in the provided list,
            # or they were never on the same squad in those matches.
            all_teammates_performance.append({
                "teammate_account_id": teammate_id,
                "teammate_name": None,
                "matches_played_together": 0,
                "avg_kills": 0.0,
                "avg_damage_dealt": 0.0,
                "avg_survival_time_seconds": 0.0,
                "avg_match_rank": 0.0, # Or some indicator like N/A
                "avg_assists": 0.0
            })
            
    return all_teammates_performance


def calculate_overall_team_stats(
    team_member_account_ids: List[str],
    processed_match_details_list: List[Dict[str, Any]],
    requested_season_id: str # For documentation, though direct filtering is challenging
) -> Dict[str, Any]:
    """
    Calculates overall team statistics when the ENTIRE identified team plays together.

    Args:
        team_member_account_ids: List of account IDs of the identified team members.
        processed_match_details_list: List of match detail objects from team_analyzer.
        requested_season_id: The specific season ID requested (see notes on filtering limitations).

    Returns:
        A dictionary containing aggregated/averaged overall team stats.
    """
    
    # Ensure there's a team to analyze (at least 2 members)
    if not team_member_account_ids or len(team_member_account_ids) < 2:
        return {
            "avg_team_kills": 0.0,
            "avg_team_damage": 0.0,
            "avg_team_survival_time": 0.0,
            "avg_team_match_rank": 0.0,
            "matches_played_as_full_team": 0,
            "message": "Not enough team members to calculate overall team stats."
        }

    total_team_kills = 0
    total_team_damage = 0
    total_team_survival_seconds = 0 # Sum of individual survival times for averaging
    total_team_match_rank = 0
    matches_played_as_full_team = 0
    
    team_member_set = set(team_member_account_ids)

    for match_details in processed_match_details_list:
        # Seasonal Filtering: As discussed, this is hard.
        # If match_details had a reliable 'seasonId' field, we'd use it:
        # if match_details.get("data",{}).get("attributes",{}).get("seasonIdFromAPI") != requested_season_id:
        #     continue

        participants_data = [item for item in match_details.get("included", []) if item["type"] == "participant"]
        rosters_data = [item for item in match_details.get("included", []) if item["type"] == "roster"]

        for roster_data in rosters_data:
            roster_participant_objects = roster_data.get("relationships", {}).get("participants", {}).get("data", [])
            roster_participant_ids_in_match = {p["id"] for p in roster_participant_objects} # These are participant_ids, not account_ids yet

            # Map participant IDs in this roster to account IDs
            current_roster_account_ids: Set[str] = set()
            roster_participant_details_map: Dict[str, Dict[str, Any]] = {} # Store participant details by account_id

            for p_detail in participants_data:
                if p_detail["id"] in roster_participant_ids_in_match:
                    acc_id = p_detail.get("attributes", {}).get("stats", {}).get("playerId")
                    if acc_id:
                        current_roster_account_ids.add(acc_id)
                        roster_participant_details_map[acc_id] = p_detail.get("attributes", {}).get("stats", {})


            # Check if this roster contains ALL members of the identified team
            if team_member_set.issubset(current_roster_account_ids):
                matches_played_as_full_team += 1
                
                current_match_team_kills = 0
                current_match_team_damage = 0
                current_match_team_survival_sum = 0
                
                for team_member_id in team_member_set:
                    member_stats = roster_participant_details_map.get(team_member_id)
                    if member_stats:
                        current_match_team_kills += member_stats.get("kills", 0)
                        current_match_team_damage += member_stats.get("damageDealt", 0.0)
                        current_match_team_survival_sum += member_stats.get("timeSurvived", 0.0)
                
                total_team_kills += current_match_team_kills
                total_team_damage += current_match_team_damage
                total_team_survival_seconds += (current_match_team_survival_sum / len(team_member_set)) # Avg survival for this match for the team members
                
                # Team rank is on the roster attributes
                rank = roster_data.get("attributes", {}).get("stats", {}).get("rank")
                if rank is None:
                    rank = roster_data.get("attributes", {}).get("rank", 0)
                total_team_match_rank += rank
                
                break # Found the team's roster for this match, no need to check other rosters in this match

    if matches_played_as_full_team > 0:
        avg_team_kills = total_team_kills / matches_played_as_full_team
        avg_team_damage = total_team_damage / matches_played_as_full_team
        avg_team_survival_time = total_team_survival_seconds / matches_played_as_full_team
        avg_team_match_rank = total_team_match_rank / matches_played_as_full_team
        message = f"Stats based on {matches_played_as_full_team} recent match(es) played as a full team."
    else:
        avg_team_kills = 0.0
        avg_team_damage = 0.0
        avg_team_survival_time = 0.0
        avg_team_match_rank = 0.0
        message = "No recent matches found where the identified team played together as a full unit."

    return {
        "avg_team_kills": round(avg_team_kills, 2),
        "avg_team_damage": round(avg_team_damage, 2),
        "avg_team_survival_time": round(avg_team_survival_time, 2),
        "avg_team_match_rank": round(avg_team_match_rank, 2),
        "matches_played_as_full_team": matches_played_as_full_team,
        "message": message
    }
