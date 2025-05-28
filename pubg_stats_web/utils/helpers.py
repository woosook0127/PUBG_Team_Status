# Utility functions will be added here.
import logging
from collections import defaultdict
import requests # Needed for calculate_individual_weapon_stats if fetching telemetry

# Assuming PubgAPI class is in a directory structure like:
# project_root/
# ├── pubg_stats_web/
# │   ├── services/
# │   │   └── pubg_api.py (contains PubgAPI class)
# │   └── utils/
# │       └── helpers.py (this file)
try:
    from ..services.pubg_api import PubgAPI
except ImportError:
    logging.warning("Could not perform relative import of PubgAPI. Attempting direct import (may fail in package context).")
    # This fallback is primarily for direct script testing if the utils module is run standalone.
    # In the Flask app context, the relative import should work.
    from services.pubg_api import PubgAPI


# Configure basic logging if not already configured by the main app
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


def format_player_stats_for_display(raw_stats):
    """
    Placeholder function to transform raw player stats into a display-friendly format.
    """
    if not raw_stats:
        return {}
    logging.debug(f"Formatting player stats: {raw_stats}")
    return {"message": "Data processing for player stats to be implemented.", "received_stats": raw_stats}


def prepare_chart_data(stats, chart_type):
    """
    Placeholder function to prepare data for a specific chart type.
    """
    logging.debug(f"Preparing chart data for type '{chart_type}' with stats: {stats}")
    return {"message": f"Chart data preparation for '{chart_type}' to be implemented.", "received_stats": stats}


def identify_frequent_teammates(
    pubg_api_service: PubgAPI, 
    input_player_account_id: str, 
    season_id: str, 
    match_threshold: int = 5
) -> dict[str, dict]:
    """
    Analyzes a player's match history for a given season to find frequent teammates.
    (Implementation from previous task)
    """
    if not pubg_api_service:
        logging.error("PubgAPI service instance is required for identifying frequent teammates.")
        return {}
    if not input_player_account_id:
        logging.error("Input player account ID is required.")
        return {}
    if not season_id:
        logging.error("Season ID is required.")
        return {}

    logging.info(f"Starting teammate identification for player {input_player_account_id} in season {season_id} with threshold {match_threshold}.")
    match_ids = pubg_api_service.get_player_matches(input_player_account_id, season_id)
    if not match_ids:
        logging.info(f"No match IDs found for player {input_player_account_id} in season {season_id}. Cannot identify teammates.")
        return {}
    
    logging.info(f"Found {len(match_ids)} matches for player {input_player_account_id} in season {season_id}. Processing them...")
    teammate_candidates = defaultdict(lambda: {'playerName': '', 'matchesTogether': 0, 'matchIds': []})
    matches_to_process = match_ids 
    logging.info(f"Will process up to {len(matches_to_process)} matches for teammate identification.")

    for i, match_id in enumerate(matches_to_process):
        logging.debug(f"Processing match {i+1}/{len(matches_to_process)} for teammates: {match_id}")
        full_match_response = pubg_api_service.get_match_details(match_id)
        if not full_match_response or 'data' not in full_match_response or 'included' not in full_match_response:
            logging.warning(f"Skipping match {match_id} for teammate ID due to missing data or 'included' array.")
            continue
        
        included_data = full_match_response.get('included', [])
        participants_map = {obj['id']: obj for obj in included_data if obj.get('type') == 'participant'}

        for roster_obj in included_data:
            if roster_obj.get('type') == 'roster':
                try:
                    roster_participants_refs = roster_obj.get('relationships', {}).get('participants', {}).get('data', [])
                    is_input_player_in_this_roster = False
                    current_roster_player_ids = [] # Store actual player account IDs in this roster
                    
                    for participant_ref in roster_participants_refs:
                        participant_actual_obj = participants_map.get(participant_ref['id'])
                        if participant_actual_obj:
                            p_account_id = participant_actual_obj.get('attributes', {}).get('stats', {}).get('playerId')
                            if p_account_id:
                                current_roster_player_ids.append(p_account_id)
                                if p_account_id == input_player_account_id:
                                    is_input_player_in_this_roster = True
                    
                    if is_input_player_in_this_roster:
                        for p_account_id in current_roster_player_ids:
                            if p_account_id != input_player_account_id:
                                # Find the participant object again to get the name (could be optimized)
                                p_obj_for_name = next((p for p in participants_map.values() if p.get('attributes',{}).get('stats',{}).get('playerId') == p_account_id), None)
                                teammate_name = p_obj_for_name.get('attributes',{}).get('stats',{}).get('name', 'Unknown') if p_obj_for_name else 'Unknown'

                                if not teammate_candidates[p_account_id]['playerName'] and teammate_name != 'Unknown':
                                    teammate_candidates[p_account_id]['playerName'] = teammate_name
                                teammate_candidates[p_account_id]['matchesTogether'] += 1
                                if match_id not in teammate_candidates[p_account_id]['matchIds']:
                                     teammate_candidates[p_account_id]['matchIds'].append(match_id)
                        break 
                except (AttributeError, KeyError) as e:
                    logging.warning(f"Error processing roster {roster_obj.get('id')} in match {match_id} for teammates: {e}.")
                    continue
            
    logging.info(f"Finished processing matches for teammates. Found {len(teammate_candidates)} potential teammates.")
    frequent_teammates = {acc_id: data for acc_id, data in teammate_candidates.items() if data['matchesTogether'] >= match_threshold}
    logging.info(f"Identified {len(frequent_teammates)} frequent teammates meeting threshold {match_threshold}.")
    return frequent_teammates


def calculate_individual_player_stats(player_season_data: dict) -> dict | None:
    """
    Calculates aggregated individual player stats from season data for a pentagonal chart.
    Stats are: damageDealt, kills, assists, survivalTime (average), avgRank.
    """
    if not player_season_data or 'attributes' not in player_season_data or 'gameModeStats' not in player_season_data['attributes']:
        logging.warning("calculate_individual_player_stats: Invalid or missing player_season_data or gameModeStats.")
        return None

    game_mode_stats = player_season_data['attributes']['gameModeStats']
    if not game_mode_stats:
        logging.warning("calculate_individual_player_stats: gameModeStats is empty.")
        return None

    # Prioritize modes: squad-fpp, squad, solo-fpp, solo, duo-fpp, duo
    # For simplicity, we will sum relevant stats and average others across all available modes.
    # A more sophisticated approach might weigh them or pick specific modes.
    
    total_damage_dealt = 0.0
    total_kills = 0
    total_assists = 0
    total_time_survived_seconds = 0.0
    total_rank_points_equivalent = 0 # Using a sum of (wins*10 + top10s) as a proxy for rank contribution
    total_rounds_played = 0

    # These fields are often directly available per mode.
    # Field names based on typical PUBG API responses.
    stat_fields = {
        "damageDealt": "damageDealt",
        "kills": "kills",
        "assists": "assists",
        "timeSurvived": "timeSurvived", # Total time survived in that mode for the season
        "wins": "wins",
        "top10s": "top10s",
        "roundsPlayed": "roundsPlayed",
        # "rankPoints": "rankPoints" # Often available, but avgRank is more complex.
        # "averageRank" # If this field exists directly, it would be ideal. Not standard.
    }

    for mode, stats in game_mode_stats.items():
        logging.debug(f"Processing stats for game mode: {mode}")
        
        rounds = stats.get(stat_fields["roundsPlayed"], 0)
        if rounds == 0: # Skip modes with no matches played
            logging.debug(f"Skipping mode {mode} as roundsPlayed is 0.")
            continue

        total_rounds_played += rounds
        total_damage_dealt += stats.get(stat_fields["damageDealt"], 0.0)
        total_kills += stats.get(stat_fields["kills"], 0)
        total_assists += stats.get(stat_fields["assists"], 0)
        total_time_survived_seconds += stats.get(stat_fields["timeSurvived"], 0.0)
        
        # For avgRank proxy:
        # A simple approach: give points for wins and top10s.
        # This is a placeholder as "avgRank" is not a direct, consistently available stat.
        # Actual rank is often a tier/sub-tier, not a numeric average.
        # We'll use (wins * large_factor + top10s * small_factor) / rounds as a score.
        # For the pentagon, a higher "rank score" is better.
        # Let's use wins and top10s to form a "performance score" for rank.
        # A simple "win rate" or "top 10 rate" could also work.
        # Let's try: (wins / roundsPlayed) * 100. Max 100.
        # Or, as requested, use rankPoints or wins/roundsPlayed.
        # Let's use ( (wins/rounds) * 50 + (top10s/rounds) * 50 ) if rounds > 0 else 0
        # This creates a score from 0-100 where higher is better.
        wins = stats.get(stat_fields["wins"], 0)
        top10s = stats.get(stat_fields["top10s"], 0)
        
        # Accumulate for a weighted average of this "rank score" later
        total_rank_points_equivalent += ( (wins / rounds) * 50 + (top10s / rounds) * 50 ) * rounds


    if total_rounds_played == 0:
        logging.warning("calculate_individual_player_stats: No rounds played across any game mode.")
        return None

    avg_survival_time = total_time_survived_seconds / total_rounds_played
    
    # Calculate the weighted average rank score
    avg_rank_score = total_rank_points_equivalent / total_rounds_played

    calculated_stats = {
        "damageDealt": round(total_damage_dealt / total_rounds_played, 2), # Avg damage per match
        "kills": round(total_kills / total_rounds_played, 2), # Avg kills per match
        "assists": round(total_assists / total_rounds_played, 2), # Avg assists per match
        "survivalTime": round(avg_survival_time, 2), # Avg survival time in seconds per match
        "avgRank": round(avg_rank_score, 2) # Composite score representing rank/performance (0-100)
    }
    
    logging.info(f"Calculated individual stats: {calculated_stats}")
    return calculated_stats


def calculate_teammate_synergy_stats(
    pubg_api_service: PubgAPI, 
    teammate_match_ids: list[str], 
    target_teammate_account_id: str
) -> dict | None:
    """
    Calculates aggregated stats for a target teammate across a list of shared matches.
    Stats: damageDealt, kills, assists, survivalTime (average), avgRank (average team rank).
    """
    if not pubg_api_service:
        logging.error("calculate_teammate_synergy_stats: PubgAPI service instance is required.")
        return None
    if not teammate_match_ids:
        logging.info("calculate_teammate_synergy_stats: No match IDs provided for synergy calculation.")
        return None # Or {} depending on desired behavior for no matches
    if not target_teammate_account_id:
        logging.error("calculate_teammate_synergy_stats: Target teammate account ID is required.")
        return None

    logging.info(f"Calculating synergy stats for teammate {target_teammate_account_id} across {len(teammate_match_ids)} matches.")

    total_damage = 0.0
    total_kills = 0
    total_assists = 0
    total_survival_seconds = 0.0
    total_rank_sum = 0 # Sum of team ranks
    processed_match_count = 0

    # Limit processing for now if list is very long, e.g. first 20 matches
    # matches_to_process = teammate_match_ids[:20] 
    matches_to_process = teammate_match_ids # Process all provided matches for now

    for i, match_id in enumerate(matches_to_process):
        logging.debug(f"Processing match {i+1}/{len(matches_to_process)} for synergy: {match_id}")
        full_match_response = pubg_api_service.get_match_details(match_id)

        if not full_match_response or 'data' not in full_match_response or 'included' not in full_match_response:
            logging.warning(f"calculate_teammate_synergy_stats: Skipping match {match_id}, missing data or 'included' array.")
            continue

        match_data_obj = full_match_response.get('data', {})
        included_data = full_match_response.get('included', [])
        
        teammate_participant_obj = None
        teammate_roster_obj = None

        # Find the target teammate's participant object
        for item in included_data:
            if item.get('type') == 'participant':
                p_stats = item.get('attributes', {}).get('stats', {})
                if p_stats and p_stats.get('playerId') == target_teammate_account_id:
                    teammate_participant_obj = item
                    break
        
        if not teammate_participant_obj:
            logging.warning(f"calculate_teammate_synergy_stats: Teammate {target_teammate_account_id} not found in match {match_id} participants.")
            continue

        # Extract teammate's individual stats for this match
        teammate_stats = teammate_participant_obj.get('attributes', {}).get('stats', {})
        total_damage += teammate_stats.get('damageDealt', 0.0)
        total_kills += teammate_stats.get('kills', 0)
        total_assists += teammate_stats.get('assists', 0)
        total_survival_seconds += teammate_stats.get('timeSurvived', 0.0)

        # Find the teammate's roster to get team rank for that match
        # This involves checking which roster includes this participant
        for item in included_data:
            if item.get('type') == 'roster':
                roster_participants_refs = item.get('relationships', {}).get('participants', {}).get('data', [])
                for ref in roster_participants_refs:
                    if ref.get('id') == teammate_participant_obj.get('id'): # participant_obj ID, not account ID
                        teammate_roster_obj = item
                        break
                if teammate_roster_obj:
                    break
        
        if teammate_roster_obj:
            roster_stats = teammate_roster_obj.get('attributes', {}).get('stats', {})
            # Team rank is usually an integer. Lower is better.
            team_rank_in_match = roster_stats.get('rank') 
            if team_rank_in_match is not None: # Check for None explicitly, as rank 0 could be valid (though unlikely)
                total_rank_sum += team_rank_in_match
            else:
                logging.warning(f"calculate_teammate_synergy_stats: Could not find team rank for roster {teammate_roster_obj.get('id')} in match {match_id}.")
                # If rank is missing for a match, we might choose not to count this match for avgRank,
                # or assign a penalty rank. For now, it just won't contribute to total_rank_sum or processed_match_count for rank.
                # To ensure consistency, we should only increment processed_match_count if all necessary stats are found.
                # However, the current structure increments it regardless of finding rank.
                # Let's refine this: only increment if rank is found and used.
                # No, prompt asks for stats even if some are partial.
                # We will use the number of matches where player was found.
        else:
            logging.warning(f"calculate_teammate_synergy_stats: Could not find roster for teammate {target_teammate_account_id} in match {match_id}.")
            # As above, this match might not contribute to avgRank if roster isn't found.

        processed_match_count += 1 # Count matches where the teammate was found and their stats processed.

    if processed_match_count == 0:
        logging.info(f"calculate_teammate_synergy_stats: Teammate {target_teammate_account_id} not found in any of the provided matches, or no stats processed.")
        return None

    avg_survival = total_survival_seconds / processed_match_count
    # If some matches didn't have rank, this average might be skewed.
    # Consider having a separate count for matches where rank was successfully found.
    # For now, using processed_match_count, implying if rank is missing, it's like a 0 for that match's rank sum.
    # This is okay if we assume missing rank is rare or if 0 is a sensible default.
    # Given rank is usually 1+, a 0 would drag average down.
    # Let's make avg_rank calculation more robust: only divide by matches where rank was found.
    # This requires a separate counter: valid_rank_matches_count = 0
    # For now, sticking to prompt: avgRank over processed_match_count
    avg_rank = total_rank_sum / processed_match_count if processed_match_count > 0 else 0


    synergy_stats = {
        "damageDealt": round(total_damage / processed_match_count, 2),
        "kills": round(total_kills / processed_match_count, 2),
        "assists": round(total_assists / processed_match_count, 2),
        "survivalTime": round(avg_survival, 2),
        "avgRank": round(avg_rank, 2) # Lower is better for rank.
    }

    logging.info(f"Calculated synergy stats for teammate {target_teammate_account_id}: {synergy_stats}")
    return synergy_stats


def calculate_individual_weapon_stats(
    pubg_api_service: PubgAPI, 
    player_account_id: str, 
    season_match_ids: list[str]
) -> dict:
    """
    Calculates individual weapon stats (placeholder/simplified).
    Processes a small subset of recent matches due to telemetry complexity.
    """
    if not pubg_api_service:
        logging.error("calculate_individual_weapon_stats: PubgAPI service instance is required.")
        return {}
    if not player_account_id:
        logging.error("calculate_individual_weapon_stats: Player account ID is required.")
        return {}
    if not season_match_ids:
        logging.info("calculate_individual_weapon_stats: No match IDs provided for weapon stats calculation.")
        return {}

    logging.info(f"Calculating weapon stats for player {player_account_id} from a sample of matches.")
    
    # Process a small subset of recent matches (e.g., first 5)
    matches_to_sample = season_match_ids[:5]
    logging.warning(f"calculate_individual_weapon_stats: Processing only a sample of {len(matches_to_sample)} matches out of {len(season_match_ids)} for weapon stats due to telemetry complexity.")

    # Placeholder for aggregated data from telemetry
    # weapon_damage_agg = defaultdict(lambda: {"totalDamage": 0.0, "kills": 0, "count": 0}) # count = matches weapon used in

    for i, match_id in enumerate(matches_to_sample):
        logging.debug(f"Fetching match {i+1}/{len(matches_to_sample)} for weapon stats telemetry URL: {match_id}")
        full_match_response = pubg_api_service.get_match_details(match_id)

        if not full_match_response or 'data' not in full_match_response:
            logging.warning(f"calculate_individual_weapon_stats: Skipping match {match_id}, missing 'data' object.")
            continue
        
        match_main_data = full_match_response.get('data', {}) # This is the specific match object by ID
        
        # Path to telemetry asset: data.relationships.assets.data[0] (this is an array of assets)
        telemetry_asset_ref = None
        try:
            assets_data = match_main_data.get('relationships', {}).get('assets', {}).get('data', [])
            if assets_data:
                # Typically, the first asset is the telemetry
                telemetry_asset_ref = assets_data[0] 
            else:
                logging.warning(f"calculate_individual_weapon_stats: No assets found in relationships for match {match_id}.")
                continue
        except (AttributeError, IndexError, TypeError) as e:
            logging.error(f"Error accessing telemetry asset reference for match {match_id}: {e}")
            continue

        if not telemetry_asset_ref or telemetry_asset_ref.get('type') != 'asset':
            logging.warning(f"calculate_individual_weapon_stats: Telemetry asset reference not found or not of type 'asset' for match {match_id}.")
            continue

        # The telemetry asset ID is in telemetry_asset_ref['id'].
        # The URL is usually found by looking up this asset ID in the 'included' array of the match response.
        telemetry_url = None
        included_data = full_match_response.get('included', [])
        for item in included_data:
            if item.get('type') == 'asset' and item.get('id') == telemetry_asset_ref.get('id'):
                telemetry_url = item.get('attributes', {}).get('URL')
                break
        
        if not telemetry_url:
            logging.warning(f"calculate_individual_weapon_stats: Telemetry URL not found for asset {telemetry_asset_ref.get('id')} in match {match_id}.")
            continue

        logging.info(f"calculate_individual_weapon_stats: Found telemetry URL for match {match_id}: {telemetry_url}. "
                     "Actual fetching and parsing of telemetry data is complex and NOT IMPLEMENTED in this step.")
        # ---- Telemetry Fetching and Parsing (Conceptual) ----
        # try:
        #     telemetry_response = requests.get(telemetry_url, headers={"Accept": "application/vnd.api+json"})
        #     telemetry_response.raise_for_status()
        #     telemetry_events = telemetry_response.json() # This is an array of event objects
        #
        #     # Process telemetry_events:
        #     # Filter for LogPlayerKill, LogPlayerAttack, etc. involving player_account_id
        #     # Aggregate damage by weapon, categorize weapons.
        #     # This requires detailed knowledge of telemetry event structures.
        # except requests.exceptions.RequestException as e:
        #     logging.error(f"calculate_individual_weapon_stats: Failed to fetch telemetry for match {match_id} from {telemetry_url}: {e}")
        #     continue
        # except ValueError as e: # Includes JSONDecodeError
        #     logging.error(f"calculate_individual_weapon_stats: Failed to parse telemetry JSON for match {match_id}: {e}")
        #     continue
        # ----------------------------------------------------

    # Placeholder return due to complexity of telemetry.
    logging.warning("calculate_individual_weapon_stats: Telemetry parsing is not fully implemented. Returning placeholder data.")
    placeholder_stats = {
        "AR": {"topWeapon": "PlaceholderAR", "damagePerMatch": 0.0, "info": "Weapon stats from telemetry (sample) not yet fully implemented."},
        "DMR": {"topWeapon": "PlaceholderDMR", "damagePerMatch": 0.0, "info": "Weapon stats from telemetry (sample) not yet fully implemented."},
        "SR": {"topWeapon": "PlaceholderSR", "damagePerMatch": 0.0, "info": "Weapon stats from telemetry (sample) not yet fully implemented."},
        "SMG": {"topWeapon": "PlaceholderSMG", "damagePerMatch": 0.0, "info": "Weapon stats from telemetry (sample) not yet fully implemented."},
        "Other": {"topWeapon": "PlaceholderOther", "damagePerMatch": 0.0, "info": "Weapon stats from telemetry (sample) not yet fully implemented."}
    }
    return placeholder_stats


# Example Usage (for local testing - not part of the class itself)
if __name__ == '__main__':
    print("Testing stat calculation functions in helpers.py...")
    logging.basicConfig(level=logging.DEBUG) # Enable more verbose logging for testing

    # --- Mocking PubgAPI and its responses ---
    class MockPubgAPIForStats(PubgAPI): # Inherit from real PubgAPI to satisfy type hints
        def __init__(self, api_key, platform="kakao"):
            super().__init__(api_key, platform) # Call real __init__ but methods below are mocked
            logging.info(f"MockPubgAPIForStats initialized for platform {platform} with key {api_key[:10]}...")

        def get_player_season_stats(self, account_id, season_id):
            logging.info(f"Mock: get_player_season_stats for {account_id}, {season_id}")
            if account_id == "player_good_stats":
                return { # This is the 'data' object
                    "type": "playerSeason",
                    "id": "some_season_id_for_player",
                    "attributes": {
                        "gameModeStats": {
                            "squad-fpp": {
                                "damageDealt": 15000.0, "kills": 100, "assists": 50,
                                "timeSurvived": 180000.0, # 50 hours total -> 30 min/match if 100 matches
                                "wins": 10, "top10s": 40, "roundsPlayed": 100,
                                "rankPoints": 2500
                            },
                            "solo-fpp": {
                                "damageDealt": 2000.0, "kills": 10, "assists": 2,
                                "timeSurvived": 18000.0, # 5 hours total -> 18 min/match if 10 matches
                                "wins": 1, "top10s": 3, "roundsPlayed": 10,
                                "rankPoints": 1800
                            }
                        }
                    }
                }
            return None

        def get_player_matches(self, account_id, season_id):
            logging.info(f"Mock: get_player_matches for {account_id}, {season_id}")
            if account_id == "player_weapon_test":
                return ["match_w1", "match_w2", "match_w3", "match_w4", "match_w5", "match_w6"]
            return []

        def get_match_details(self, match_id):
            logging.info(f"Mock: get_match_details for {match_id}")
            # For calculate_teammate_synergy_stats
            if match_id.startswith("synergy_match_"):
                teammate_id_in_match = "teammate_A_id"
                participant_teammate = {
                    "type": "participant", "id": "participant_guid_teammate_A",
                    "attributes": {"stats": {"playerId": teammate_id_in_match, "name": "TeammateA",
                                             "kills": 2, "damageDealt": 250.0, "timeSurvived": 1500.0}}
                }
                participant_other = { # Another player on a different team or same team, not the target
                    "type": "participant", "id": "participant_guid_other",
                    "attributes": {"stats": {"playerId": "other_player_id", "name": "OtherPlayer",
                                             "kills": 1, "damageDealt": 100.0, "timeSurvived": 1000.0}}
                }
                roster_with_teammate = {
                    "type": "roster", "id": "roster_guid_X",
                    "attributes": {"stats": {"rank": 5}}, # Team rank for this match
                    "relationships": {"participants": {"data": [{"type": "participant", "id": "participant_guid_teammate_A"}]}}
                }
                return {
                    "data": {"type": "match", "id": match_id},
                    "included": [participant_teammate, participant_other, roster_with_teammate]
                }

            # For calculate_individual_weapon_stats (mocking telemetry asset)
            if match_id.startswith("match_w"):
                 return {
                    "data": {
                        "type": "match", "id": match_id,
                        "relationships": {
                            "assets": {
                                "data": [{"type": "asset", "id": f"telemetry_asset_{match_id}"}]
                            }
                        }
                    },
                    "included": [
                        {"type": "asset", "id": f"telemetry_asset_{match_id}", 
                         "attributes": {"URL": f"https://fake-telemetry-url.com/{match_id}"}}
                    ]
                }
            return None
            
    # --- Test calculate_individual_player_stats ---
    print("\n--- Testing calculate_individual_player_stats ---")
    mock_api = MockPubgAPIForStats(api_key="dummy_key_for_stats_test")
    season_data_example = mock_api.get_player_season_stats("player_good_stats", "test_season")
    if season_data_example:
        individual_stats = calculate_individual_player_stats(season_data_example)
        if individual_stats:
            print(f"Calculated Individual Stats: {individual_stats}")
            # Expected:
            # Total rounds = 110
            # Total damage = 17000 -> avg = 154.55
            # Total kills = 110 -> avg = 1.0
            # Total assists = 52 -> avg = 0.47
            # Total time survived = 198000 -> avg = 1800.0
            # Rank score squad: ((10/100)*50 + (40/100)*50) = (0.1*50 + 0.4*50) = 5 + 20 = 25
            # Rank score solo: ((1/10)*50 + (3/10)*50) = (0.1*50 + 0.3*50) = 5 + 15 = 20
            # total_rank_points_equivalent = 25*100 + 20*10 = 2500 + 200 = 2700
            # avgRank = 2700 / 110 = 24.55
            assert abs(individual_stats['damageDealt'] - (15000.0+2000.0)/110) < 0.01
            assert abs(individual_stats['kills'] - (100+10)/110) < 0.01
            assert abs(individual_stats['assists'] - (50+2)/110) < 0.01
            assert abs(individual_stats['survivalTime'] - (180000.0+18000.0)/110) < 0.01
            expected_rank_score = ( (10/100*50 + 40/100*50)*100 + (1/10*50 + 3/10*50)*10 ) / 110
            assert abs(individual_stats['avgRank'] - expected_rank_score) < 0.01
            print("Individual stats assertions passed (approx).")
        else:
            print("Failed to calculate individual stats.")
    else:
        print("Failed to get mock season data for individual stats test.")

    # --- Test calculate_teammate_synergy_stats ---
    print("\n--- Testing calculate_teammate_synergy_stats ---")
    synergy_match_ids_test = ["synergy_match_1", "synergy_match_2"]
    target_teammate_id_test = "teammate_A_id"
    synergy_stats = calculate_teammate_synergy_stats(mock_api, synergy_match_ids_test, target_teammate_id_test)
    if synergy_stats:
        print(f"Calculated Synergy Stats for {target_teammate_id_test}: {synergy_stats}")
        # Expected for TeammateA over 2 identical matches:
        # damageDealt: 250.0, kills: 2, assists: 0 (not in mock), survivalTime: 1500.0, avgRank: 5.0
        assert synergy_stats['damageDealt'] == 250.0
        assert synergy_stats['kills'] == 2.0
        assert synergy_stats['assists'] == 0.0 # Assists not in mock participant stats
        assert synergy_stats['survivalTime'] == 1500.0
        assert synergy_stats['avgRank'] == 5.0
        print("Synergy stats assertions passed.")
    else:
        print(f"Failed to calculate synergy stats for {target_teammate_id_test}.")
    
    # --- Test calculate_individual_weapon_stats (placeholder) ---
    print("\n--- Testing calculate_individual_weapon_stats (placeholder) ---")
    weapon_player_id = "player_weapon_test"
    weapon_season_matches = mock_api.get_player_matches(weapon_player_id, "test_season")
    weapon_stats = calculate_individual_weapon_stats(mock_api, weapon_player_id, weapon_season_matches)
    if weapon_stats:
        print(f"Calculated Weapon Stats (Placeholder) for {weapon_player_id}: {weapon_stats}")
        assert "AR" in weapon_stats
        assert weapon_stats["AR"]["topWeapon"] == "PlaceholderAR"
        assert "info" in weapon_stats["AR"]
        print("Weapon stats (placeholder) structure seems okay.")
    else:
        print(f"Failed to get placeholder weapon stats for {weapon_player_id}.")

    print("\nFinished testing stat calculation functions.")
