# Configuration for team identification
NUM_MATCHES_TO_ANALYZE = 20  # Reduced from 50 to manage API calls during development/testing. Can be increased.
MIN_GAMES_FOR_FREQUENT_TEAM = 3 # Reduced from 5 for testing, means a squad must appear in at least 3 of the analyzed matches.
MIN_CLAN_GAMES_THRESHOLD = 3    # Minimum games with at least one other clan member to be considered as a potential primary team.

# Imports - will be added as needed
import asyncio
from collections import Counter, defaultdict
from typing import List, Dict, Set, FrozenSet, Optional, Tuple

# No longer using dummy functions, will use the passed pubg_api_module directly.
# from .. import pubg_api # This would be the ideal way if team_analyzer is a submodule.
                         # For now, pubg_api module is passed as an argument.

# Main logic will go here
async def identify_player_team(
    main_player_account_id: str, 
    platform_shard: str, 
    pubg_api_module: Any
) -> Tuple[Optional[List[str]], str, List[Dict[str, Any]]]:
    """
    Identifies a player's primary team based on clan membership and recent match history.
    Returns a tuple: (list of team member account IDs or None, identification_method_message, list_of_processed_match_details).
    The pubg_api_module is passed in to allow using the actual API functions.
    """
    clan_team_ids: Optional[List[str]] = None
    clan_member_set: Set[str] = set()
    identification_message = "No consistent team identified."

    # Step 2a: Fetch Clan Information
    try:
        clan_details = await pubg_api_module.get_player_clan_details(main_player_account_id, platform_shard)
        if clan_details and "data" in clan_details and clan_details["data"].get("id"):
            # Clan information is often in `data.relationships.clanMembers.data` or similar
            # For this example, let's assume `get_player_clan_details` is modified or already returns members directly for simplicity
            # Or, we might need another call to /clans/{clanId} and then get members.
            # The existing `get_player_clan_details` in the project seems to fetch clan ID and then clan details,
            # which should include members.
            # Let's assume clan_details response from `get_player_clan_details` looks like:
            # { "data": { "attributes": { "name": "ClanName" }, "relationships": { "members": { "data": [ { "type": "player", "id": "member1_id"}, ... ] } } } }
            # This structure needs to be confirmed with the actual API response of `get_player_clan_details`
            
            # Based on the provided `get_player_clan_details` which fetches clan details using clan ID:
            # The response would be for the clan itself.
            # Example structure for clan details:
            # { "data": { "attributes": {"clanName": "Cool Clan", "clanTag": "COOL"},
            #             "relationships": { "members": { "data": [ {"type": "player", "id": "account.xxxx1"}, ... ] } } } }
            
            clan_members_data = clan_details.get("data", {}).get("relationships", {}).get("members", {}).get("data", [])
            if clan_members_data:
                # Filter out the main player from their own clan list for some comparisons later,
                # but for the "clan_team_ids" it should include everyone in the clan.
                clan_team_ids = sorted(list(set(member['id'] for member in clan_members_data)))
                clan_member_set = set(clan_team_ids)
                # Remove main_player_account_id for certain checks (e.g. "played with other clan member")
                # clan_member_set_excluding_main_player = clan_member_set - {main_player_account_id}
                print(f"[TEAM_ANALYZER] Player {main_player_account_id} is in clan with members: {clan_team_ids}")
            else:
                print(f"[TEAM_ANALYZER] Player {main_player_account_id} is in a clan, but no member data found in response: {clan_details}")
        elif clan_details and clan_details.get("message") and "not in a clan" in clan_details["message"]:
            print(f"[TEAM_ANALYZER] Player {main_player_account_id} is not in a clan.")
        elif "error" in clan_details:
            print(f"[TEAM_ANALYZER] Error fetching clan details: {clan_details.get('error')}")
            # Potentially raise an error or handle as "not in clan" for robustness
    except Exception as e:
        print(f"[TEAM_ANALYZER] Exception fetching clan details: {e}")
        # Consider player not in a clan or error in fetching

    # Step 2b: Analyze Match History for Frequent Teammates
    squad_play_counts: Dict[FrozenSet[str], int] = defaultdict(int)
    processed_match_details_list: List[Dict[str, Any]] = [] # To store successfully fetched match details

    match_ids_fetched = await pubg_api_module.get_player_match_history_ids(main_player_account_id, platform_shard)
    
    if isinstance(match_ids_fetched, dict) and "error" in match_ids_fetched:
        print(f"[TEAM_ANALYZER] Error fetching match history: {match_ids_fetched.get('error')}")
        return None, f"Error fetching match history: {match_ids_fetched.get('details', 'Unknown error')}", []

    if not match_ids_fetched:
        print(f"[TEAM_ANALYZER] No match history found for {main_player_account_id}.")
        if clan_team_ids and len(clan_team_ids) > 1:
             return clan_team_ids, f"Identified by clan membership (no match history analyzed).", []
        return None, "No match history found to analyze.", []


    match_ids_to_analyze = match_ids_fetched[:NUM_MATCHES_TO_ANALYZE]
    print(f"[TEAM_ANALYZER] Analyzing {len(match_ids_to_analyze)} matches for player {main_player_account_id}...")

    actual_matches_analyzed_count = 0
    clan_team_play_frequency = 0

    # Using asyncio.gather to fetch match details concurrently, respecting rate limiter in pubg_api
    match_detail_tasks = [pubg_api_module.get_match_details(match_id, platform_shard) for match_id in match_ids_to_analyze]
    match_details_results = await asyncio.gather(*match_detail_tasks, return_exceptions=True)


    for i, match_details_or_exception in enumerate(match_details_results):
        match_id = match_ids_to_analyze[i] # Get corresponding match_id
        try:
            if isinstance(match_details_or_exception, Exception):
                # Handle exceptions from get_match_details (e.g., network error, specific HTTP error not caught inside)
                print(f"[TEAM_ANALYZER] Exception fetching details for match {match_id}: {match_details_or_exception}")
                # Optionally, log this exception or re-raise if critical
                continue # Skip this match

            match_details = match_details_or_exception # Result is not an exception
            
            if "error" in match_details or not match_details.get("data"):
                print(f"[TEAM_ANALYZER] Error or no data fetching details for match {match_id}: {match_details.get('error', 'No data')}")
                continue
            
            # Store successfully fetched and valid match_details
            # We store it early, so even if player not found in this match (e.g. data issue), we have it
            # However, for team performance, we only care about matches where the player participated meaningfully.
            # Let's add it to processed_match_details_list later, only if player is found in the match.

            # Find main player's roster and their squad members
            main_player_participant_id: Optional[str] = None
            # Filter participants and rosters from the 'included' array once
            participants_data = [item for item in match_details.get("included", []) if item["type"] == "participant"]
            rosters_data = [item for item in match_details.get("included", []) if item["type"] == "roster"]

            for p_data in participants_data:
                if p_data.get("attributes", {}).get("stats", {}).get("playerId") == main_player_account_id:
                    main_player_participant_id = p_data["id"]
                    break
            
            if not main_player_participant_id:
                print(f"[TEAM_ANALYZER] Main player {main_player_account_id} not found in participants for match {match_id}. Skipping analysis for this match.")
                continue # Skip this match for squad counting, but it was fetched. Add to processed_match_details_list? No, if player not found, less relevant.

            # If player is found, this match is relevant for analysis
            actual_matches_analyzed_count +=1
            processed_match_details_list.append(match_details) # Add to list for potential later use

            current_match_squad_account_ids: Set[str] = set()
            found_squad = False
            for roster_data in rosters_data:
                roster_participant_ids = {p["id"] for p in roster_data.get("relationships", {}).get("participants", {}).get("data", [])}
                if main_player_participant_id in roster_participant_ids:
                    found_squad = True
                    for p_id_obj in roster_data.get("relationships", {}).get("participants", {}).get("data", []):
                        p_participant_id = p_id_obj["id"]
                        for p_data_lookup in participants_data: # Search within the filtered list
                            if p_data_lookup["id"] == p_participant_id:
                                squad_member_account_id = p_data_lookup.get("attributes", {}).get("stats", {}).get("playerId")
                                if squad_member_account_id: 
                                    current_match_squad_account_ids.add(squad_member_account_id)
                                break
                    break 

            if not found_squad or not current_match_squad_account_ids:
                print(f"[TEAM_ANALYZER] Could not determine squad for {main_player_account_id} in match {match_id}. Skipping squad count for this match.")
                # Match still added to processed_match_details_list if player was found.
                continue

            if 1 < len(current_match_squad_account_ids) <= 5: 
                squad_key = frozenset(current_match_squad_account_ids)
                squad_play_counts[squad_key] += 1
            
            if clan_member_set: 
                other_clan_members_in_squad = current_match_squad_account_ids.intersection(clan_member_set) - {main_player_account_id}
                if other_clan_members_in_squad:
                    clan_team_play_frequency += 1
        
        except Exception as e: # Should catch exceptions not caught by asyncio.gather's return_exceptions
            print(f"[TEAM_ANALYZER] General exception processing match {match_id}: {e}")


    if actual_matches_analyzed_count == 0: # This means no matches had the main player or all failed processing
        message_if_no_matches = "No matches could be successfully analyzed where the player was found."
        if not (clan_team_ids and len(clan_team_ids) > 1):
            print(f"[TEAM_ANALYZER] {message_if_no_matches}")
            return None, message_if_no_matches, processed_match_details_list # Return whatever was processed
        else: # Clan exists, but no matches analyzed
             return clan_team_ids, f"Identified by clan membership ({message_if_no_matches})", processed_match_details_list

    # Step 2c: Determine Most Frequent Squad
    most_frequent_squad_ids: Optional[List[str]] = None
    most_frequent_squad_play_frequency = 0

    if squad_play_counts:
        for squad_ids_set, count in squad_play_counts.items():
            if 2 <= len(squad_ids_set) <= 5 and count >= MIN_GAMES_FOR_FREQUENT_TEAM:
                if count > most_frequent_squad_play_frequency:
                    most_frequent_squad_play_frequency = count
                    most_frequent_squad_ids = sorted(list(squad_ids_set))
                elif count == most_frequent_squad_play_frequency:
                    most_frequent_squad_ids = sorted(list(squad_ids_set)) 

    chosen_team: Optional[List[str]] = None
    clan_is_viable = clan_team_ids and len(clan_team_ids) > 1 and clan_team_play_frequency >= MIN_CLAN_GAMES_THRESHOLD
    squad_is_viable = most_frequent_squad_ids and most_frequent_squad_play_frequency >= MIN_GAMES_FOR_FREQUENT_TEAM
    
    final_identification_message = ""

    if clan_is_viable and squad_is_viable:
        if clan_team_play_frequency >= most_frequent_squad_play_frequency:
            chosen_team = clan_team_ids
            final_identification_message = f"Identified by clan membership (played together in {clan_team_play_frequency}/{actual_matches_analyzed_count} analyzed matches)."
        else:
            chosen_team = most_frequent_squad_ids
            final_identification_message = f"Identified by frequent squad (played together in {most_frequent_squad_play_frequency}/{actual_matches_analyzed_count} analyzed matches)."
    elif clan_is_viable:
        chosen_team = clan_team_ids
        final_identification_message = f"Identified by clan membership (played together in {clan_team_play_frequency}/{actual_matches_analyzed_count} analyzed matches; no other frequent squad found)."
    elif squad_is_viable:
        chosen_team = most_frequent_squad_ids
        final_identification_message = f"Identified by frequent squad (played together in {most_frequent_squad_play_frequency}/{actual_matches_analyzed_count} analyzed matches; no qualifying clan activity)."
    else:
        if clan_team_ids and len(clan_team_ids) == 1 and clan_team_ids[0] == main_player_account_id:
             final_identification_message = "Player is in a solo clan. No other team members identified."
        else:
             final_identification_message = f"No consistent team identified meeting frequency thresholds (Clan: {clan_team_play_frequency}/{MIN_CLAN_GAMES_THRESHOLD} games, Squad: {most_frequent_squad_play_frequency}/{MIN_GAMES_FOR_FREQUENT_TEAM} games out of {actual_matches_analyzed_count} analyzed)."
    
    print(f"[TEAM_ANALYZER] Clan viable: {clan_is_viable} (Played {clan_team_play_frequency} games with clan members out of {actual_matches_analyzed_count} analyzed matches)")
    print(f"[TEAM_ANALYZER] Frequent squad viable: {squad_is_viable} (Most frequent squad played {most_frequent_squad_play_frequency} games)")
    print(f"[TEAM_ANALYZER] Identification: {final_identification_message}")
    
    return chosen_team, final_identification_message, processed_match_details_list


async def _test_identify_player_team():
    # Mock API module
    class MockPubgApi:
        async def get_player_clan_details(self, account_id: str, platform_shard: str):
            print(f"Mock: get_player_clan_details for {account_id}")
            if account_id == "player_with_clan_and_squad": # Player in clan, also plays with another squad
                return {"data": {"id": "clan1", "attributes": {"clanName": "Test Clan"}, 
                                 "relationships": {"members": {"data": [
                                     {"type": "player", "id": "player_with_clan_and_squad"},
                                     {"type": "player", "id": "clan_mate1"},
                                     {"type": "player", "id": "clan_mate2"}
                                 ]}}}}
            elif account_id == "player_only_in_clan":
                return {"data": {"id": "clan2", "attributes": {"clanName": "Solo Clan"},
                                 "relationships": {"members": {"data": [
                                     {"type": "player", "id": "player_only_in_clan"},
                                     {"type": "player", "id": "clan_mate_A"},
                                     {"type": "player", "id": "clan_mate_B"}
                                 ]}}}}
            return {"message": "Player not in clan"}

        async def get_player_match_history_ids(self, account_id: str, platform_shard: str):
            print(f"Mock: get_player_match_history_ids for {account_id}")
            return [f"m{i}" for i in range(NUM_MATCHES_TO_ANALYZE)] # Default 20 matches

        async def get_match_details(self, match_id: str, platform_shard: str):
            # print(f"Mock: get_match_details for {match_id}")
            # Player: "player_with_clan_and_squad" (main focus)
            # Clanmates: "clan_mate1", "clan_mate2"
            # Frequent squadmates: "friend1", "friend2"

            # Scenario: 5 games with clan, 10 games with friends, 5 solo/random
            match_num = int(match_id[1:])
            
            participants = [{"type": "participant", "id": "p_main", "attributes": {"stats": {"playerId": "player_with_clan_and_squad"}}}]
            roster_participants_data = [{"id": "p_main"}]

            if match_num < 5: # Play with clan
                participants.extend([
                    {"type": "participant", "id": "p_cm1", "attributes": {"stats": {"playerId": "clan_mate1"}}},
                    {"type": "participant", "id": "p_cm2", "attributes": {"stats": {"playerId": "clan_mate2"}}},
                ])
                roster_participants_data.extend([{"id": "p_cm1"}, {"id": "p_cm2"}])
            elif match_num < 15: # Play with friends (10 games)
                participants.extend([
                    {"type": "participant", "id": "p_f1", "attributes": {"stats": {"playerId": "friend1"}}},
                    {"type": "participant", "id": "p_f2", "attributes": {"stats": {"playerId": "friend2"}}},
                ])
                roster_participants_data.extend([{"id": "p_f1"}, {"id": "p_f2"}])
            else: # Play with random
                participants.append({"type": "participant", "id": "p_rand", "attributes": {"stats": {"playerId": "random_player"}}})
                roster_participants_data.append({"id": "p_rand"})

            return {"data": {"type": "match", "id": match_id, "attributes": {"seasonState": "progress"}}, # Assuming a way to check season
                    "included": participants + [{"type": "roster", "id": "r1", "relationships": {"participants": {"data": roster_participants_data}}}]}

    print("--- Test: Player with Clan and Frequent Squad (Squad More Frequent) ---")
    # Ensure constants are set for this test: NUM_MATCHES_TO_ANALYZE=20, MIN_GAMES_FOR_FREQUENT_TEAM=3, MIN_CLAN_GAMES_THRESHOLD=3
    # Expected: Frequent squad (player, friend1, friend2) because they played 10 times vs 5 times with clan.
    team, msg, matches = await identify_player_team("player_with_clan_and_squad", "steam", MockPubgApi())
    print(f"Team: {team}, Msg: {msg}, Matches processed: {len(matches)}")
    assert team and "friend1" in team and "friend2" in team
    assert "frequent squad" in msg.lower()
    assert len(matches) > 0 # Make sure matches are returned

    # Add more test cases if needed: only clan, no team, tie-breaking etc.

# if __name__ == "__main__":
#     # This is just for local testing of identify_player_team
#     # Ensure NUM_MATCHES_TO_ANALYZE, etc., are set appropriately for the test scenario.
#     asyncio.run(_test_identify_player_team())
