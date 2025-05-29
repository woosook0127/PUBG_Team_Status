import json
import os
import sys
import logging

# Adjust sys.path to allow importing from pubg_stats_web
# Assumes this script is in the root directory (/app)
# and pubg_stats_web is a subdirectory.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from pubg_stats_web.services.pubg_api import PubgAPI
except ImportError as e:
    print(f"Error importing PubgAPI: {e}")
    print("Please ensure that pubg_stats_web is in your PYTHONPATH or this script is run from the project root.")
    sys.exit(1)

# --- Configuration (To be filled in by the person running the script) ---
# It's critical to use a KAKAO platform API key and a player/season from that platform.
# Using a key from a different platform (e.g., Steam) with Kakao player names will likely fail.
API_KEY = "YOUR_KAKAO_API_KEY_HERE"  # Replace with a valid KAKAO platform API Key
PLAYER_NAME = "PLAYER_NAME_HERE"      # Replace with a valid Kakao player name
# Example: "division.bro.official.pc-2018-08" (this is old, find a recent one from get_seasons)
# To get a recent season_id:
# 1. Temporarily uncomment the get_seasons call below in a test PubgAPI instance.
# 2. Run the script with a valid API key.
# 3. Pick a recent season ID from the output (e.g., one where isCurrentSeason is true).
SEASON_ID = "RECENT_KAKAO_SEASON_ID_HERE" # Replace with a recent Kakao season ID

# Configure basic logging for the PubgAPI service (optional, but helpful)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

def fetch_and_print_sample_match_details(api_key, player_name, season_id):
    """
    Fetches and prints details for the first match found for a given player and season.
    """
    if api_key == "YOUR_KAKAO_API_KEY_HERE" or player_name == "PLAYER_NAME_HERE" or season_id == "RECENT_KAKAO_SEASON_ID_HERE":
        print("ERROR: Please update API_KEY, PLAYER_NAME, and SEASON_ID placeholders in the script before running.")
        return

    print(f"Initializing PubgAPI for platform kakao...")
    pubg_service = PubgAPI(api_key=api_key, platform="kakao") # Ensure platform is kakao

    # --- Optional: Fetch and print available seasons to help find a SEASON_ID ---
    # print("\n--- Fetching available seasons ---")
    # seasons = pubg_service.get_seasons()
    # if seasons:
    #     print(f"Found {len(seasons)} seasons. Recent seasons:")
    #     for season in seasons[:15]: # Print some recent ones
    #         is_current = season.get('attributes', {}).get('isCurrentSeason', False)
    #         print(f"  ID: {season.get('id')}, Type: {season.get('type')}, IsCurrent: {is_current}")
    #     print("Please update SEASON_ID with a recent season ID from above if needed.")
    # else:
    #     print("Could not fetch seasons. Ensure API key is valid for the Kakao platform.")
    # print("--- End of seasons list ---\n")
    # return # Comment this out after you have a season ID

    print(f"Fetching player ID for: {player_name}")
    account_id = pubg_service.get_player_id(player_name)

    if not account_id:
        print(f"Could not retrieve account ID for player: {player_name}. "
              f"Ensure the player name is correct and exists on the Kakao platform.")
        return
    print(f"Found Account ID: {account_id}")

    print(f"Fetching match list for account {account_id}, season {season_id}...")
    # The get_player_matches in the provided code internally calls get_player_season_stats without a filter.
    # This is fine, as we just need any match.
    match_ids = pubg_service.get_player_matches(account_id, season_id)

    if not match_ids:
        print(f"No matches found for account {account_id} in season {season_id}. "
              f"The player might not have played in this season, or the season ID is incorrect/old.")
        return
    
    print(f"Found {len(match_ids)} matches. Taking the first one.")
    sample_match_id = match_ids[0]
    print(f"Fetching details for match ID: {sample_match_id}")

    match_details = pubg_service.get_match_details(sample_match_id)

    if not match_details:
        print(f"Could not retrieve details for match ID: {sample_match_id}.")
        return

    print("\n--- Sample Match Details ---")
    # Print the entire match_details for thoroughness, then specific parts.
    # print(json.dumps(match_details, indent=4)) 
    
    if 'data' in match_details and 'attributes' in match_details['data']:
        print("\n--- Relevant Match Attributes (data.attributes) ---")
        print(json.dumps(match_details['data']['attributes'], indent=4))
    else:
        print("Match details structure is not as expected (missing data.attributes). Full details printed above.")

    # Also, check 'included' for participant rank/stats if needed, though attributes usually has matchType.
    # For now, focusing on data.attributes as per instructions.
    # Example:
    # if 'included' in match_details:
    #     print("\n--- Sample from 'included' array (first participant) ---")
    #     for item in match_details['included']:
    #         if item.get('type') == 'participant':
    #             print(json.dumps(item, indent=4))
    #             break # Just print one participant

if __name__ == "__main__":
    fetch_and_print_sample_match_details(API_KEY, PLAYER_NAME, SEASON_ID)
