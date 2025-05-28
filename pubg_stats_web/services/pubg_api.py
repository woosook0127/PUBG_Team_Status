import requests
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PubgAPI:
    def __init__(self, api_key, platform="kakao"):
        self.api_key = api_key
        self.platform_shard = platform # Store platform for clarity, though currently hardcoded to kakao in base_url
        self.base_url = f"https://api.pubg.com/shards/{platform}" # Use the platform parameter
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }
        if not self.api_key:
            logging.error("PubgAPI initialized without an API key. API calls will fail.")
            # This state should ideally be prevented by the calling code (app.py)

    def _request(self, endpoint, params=None):
        """Helper function to make requests to the PUBG API."""
        if not self.api_key:
            logging.error(f"API key not available for request to {endpoint}")
            return None, "API Key not configured"

        url = f"{self.base_url}/{endpoint}"
        logging.info(f"Requesting {url} with params: {params}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json(), None  # Return data and no error
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err} - Status: {response.status_code}"
            try:
                # Try to get more details from PUBG API's JSON error response
                error_details = response.json()
                error_message += f" - Details: {error_details}"
            except ValueError: # If response is not JSON
                error_message += f" - Response text: {response.text}"
            logging.error(error_message)
            return None, error_message
        except requests.exceptions.RequestException as req_err:
            # For other requests issues like network problems, timeouts
            error_message = f"Request exception occurred: {req_err}"
            logging.error(error_message)
            return None, error_message
        except Exception as e:
            # Catch any other unexpected errors
            error_message = f"An unexpected error occurred during API request: {e}"
            logging.error(error_message)
            return None, error_message

    def get_player_id(self, player_name: str) -> str | None:
        """
        Fetches the account ID for a given player name.
        Endpoint: GET /players?filter[playerNames]={playerName}
        """
        if not player_name:
            logging.warning("get_player_id called with no player_name.")
            return None
        
        endpoint = "players"
        params = {'filter[playerNames]': player_name}
        data, error = self._request(endpoint, params=params)

        if error:
            logging.error(f"Error getting player ID for {player_name}: {error}")
            return None
        
        if data and data.get('data') and len(data['data']) > 0:
            # According to JSON:API spec, 'data' is an array for collections
            return data['data'][0]['id']
        else:
            logging.warning(f"Player not found or unexpected response for {player_name}. Data: {data}")
            return None

    def get_seasons(self) -> list:
        """
        Fetches the list of available seasons for the platform.
        Endpoint: GET /seasons
        """
        endpoint = "seasons"
        data, error = self._request(endpoint)

        if error:
            logging.error(f"Error getting seasons: {error}")
            return []
        
        if data and data.get('data'):
            # Expects data to be a list of season objects
            return data['data']
        else:
            logging.warning(f"No seasons data found or unexpected response. Data: {data}")
            return []

    def get_player_season_stats(self, account_id: str, season_id: str) -> dict | None:
        """
        Fetches player statistics for a specific season.
        Endpoint: GET /players/{accountId}/seasons/{seasonId}
        This method fetches data for all game modes played by the player in the season.
        Returns the 'data' object from the JSON:API response, which includes attributes and relationships.
        """
        if not account_id or not season_id:
            logging.warning("get_player_season_stats called with missing account_id or season_id.")
            return None

        endpoint = f"players/{account_id}/seasons/{season_id}"
        data, error = self._request(endpoint)

        if error:
            logging.error(f"Error getting player season stats for account {account_id}, season {season_id}: {error}")
            return None
        
        if data and data.get('data'):
            # The 'data' object itself contains attributes (like gameModeStats)
            # and potentially relationships (like matches)
            return data['data'] 
        else:
            logging.warning(f"No season stats data found for account {account_id}, season {season_id}. Data: {data}")
            return None

    def get_player_matches(self, account_id: str, season_id: str) -> list[str]:
        """
        Fetches a list of match IDs for a player for a specific season.
        Strategy 1: Attempts to extract match IDs from the player season stats response.
        """
        logging.info(f"Attempting to get player matches for account {account_id}, season {season_id} using Strategy 1.")
        # Pass the game_mode_filter if it exists. 
        # For this subtask, we are reverting get_player_season_stats, so it won't have game_mode_filter.
        # However, if get_player_matches was intended to use a filter, it would need to be passed here.
        # For now, assuming get_player_season_stats (reverted) is called without filter.
        player_season_data = self.get_player_season_stats(account_id, season_id)

        if player_season_data:
            # JSON:API structure: player_season_data is the 'data' object from the response.
            # Match relationships are typically under 'relationships'.
            # Example path: player_season_data['relationships']['matches']['data']
            # Each item in this list would be a match identifier object, like {'type': 'match', 'id': 'match_id_here'}
            
            relationships = player_season_data.get('relationships')
            if relationships and 'matches' in relationships and 'data' in relationships['matches']:
                match_ids = [match_obj['id'] for match_obj in relationships['matches']['data'] if 'id' in match_obj]
                if match_ids:
                    logging.info(f"Found {len(match_ids)} match IDs in season stats for account {account_id}, season {season_id}.")
                    return match_ids
                else:
                    logging.info(f"Match data present in relationships but no match IDs found for account {account_id}, season {season_id}.")
                    return []
            else:
                logging.info(f"No 'matches' relationship found in season stats for account {account_id}, season {season_id}. Relationships: {relationships}")
                # Fallback or further strategy could be implemented here if needed.
                # For now, returning empty list as per subtask instructions if not directly found.
                return []
        else:
            logging.warning(f"Could not retrieve player season stats for account {account_id}, season {season_id}, so cannot extract matches.")
            return []

    def get_match_details(self, match_id: str) -> dict | None:
        """
        Fetches detailed information for a single match_id.
        Endpoint: GET /matches/{matchId}
        Returns the 'data' object from the JSON:API response.
        """
        if not match_id:
            logging.warning("get_match_details called with no match_id.")
            return None

        endpoint = f"matches/{match_id}"
        data, error = self._request(endpoint) # data here is the full JSON response

        if error:
            logging.error(f"Error getting match details for match {match_id}: {error}")
            return None
        
        if data: # data is the full JSON response from _request
            # The primary data for the match itself is in data.get('data')
            # The 'included' array contains related resources like participants and rosters
            if data.get('data'): # Check if primary data exists
                return data # Return the full JSON response
            else:
                logging.warning(f"Match details response for {match_id} is missing the primary 'data' object. Full response: {data}")
                return None
        else:
            # Error already logged by _request if data is None due to API error
            logging.warning(f"No match details data found for match {match_id} (data was None or error occurred).")
            return None

# Example Usage (for local testing - not part of the class itself, and needs API_KEY)
if __name__ == '__main__':
    # This section is for demonstration and direct testing of the class.
    # In the actual application, PubgAPI will be instantiated in app.py with the key from .env.
    print("Running PubgAPI local test examples...")
    
    # IMPORTANT: To run this test block, you MUST provide an API key.
    # You can hardcode it here for quick testing, or load it from a .env file.
    # For safety, DO NOT COMMIT a hardcoded API key.
    # Example of loading from .env if you have python-dotenv installed:
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # TEST_API_KEY = os.getenv("PUBG_API_KEY_KAKAO") # Assuming you have a KAKAO specific key in .env
    
    TEST_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ZGRmZjNhMC0xOWE4LTAxM2UtNWQ1YS0wMmE4MzJlYWU5ZTEiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzQ3OTY1OTQ3LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1hY2QxZWU4ZS01ZmNmLTQ2ODgtOTEwYy0xOTE4Y2Y3OTUwNWIifQ.WsX8ac86_fKIjDQwIsvpa_5UOadW322uI3Pl5HeAci4" # Replace with your actual key for testing

    if not TEST_API_KEY:
        print("TEST_API_KEY not set. Skipping PubgAPI method tests.")
    else:
        print(f"Using API Key starting with: {TEST_API_KEY[:10]}...")
        pubg_service = PubgAPI(api_key=TEST_API_KEY, platform="kakao")

        # --- Test get_seasons ---
        print("\n--- Testing get_seasons ---")
        seasons = pubg_service.get_seasons()
        if seasons:
            print(f"Found {len(seasons)} seasons. First few season IDs:")
            for i, season in enumerate(seasons[:3]): # Print first 3 seasons
                print(f"  ID: {season.get('id')}, Type: {season.get('type')}, IsCurrent: {season.get('attributes', {}).get('isCurrentSeason')}")
            
            # Find a current, non-offseason PC season for further tests
            current_pc_season = next((s for s in seasons if 'pc' in s['id'] and s['attributes'].get('isCurrentSeason') and not s['attributes'].get('isOffseason')), None)
            test_season_id = current_pc_season['id'] if current_pc_season else None
            if test_season_id:
                 print(f"Identified current PC season for testing: {test_season_id}")
            else:
                # Fallback to a known recent Kakao PC season if no current one is flagged (API data can vary)
                # This is an example, actual season IDs change over time.
                # You might need to update this ID by checking the output of get_seasons()
                test_season_id = "division.bro.official.pc-2018-15" 
                print(f"Could not identify a current PC season automatically, using fallback: {test_season_id} (this might be outdated)")

        else:
            print("No seasons returned or an error occurred.")
            test_season_id = None # Cannot proceed with tests needing a season ID

        # --- Test get_player_id ---
        # Replace "BATTLEGROUNDS_PLAYER_NAME_HERE" with an actual Kakao PUBG player name
        # For example, a known pro player or your own Kakao account if you have one.
        # Note: Player names are case-sensitive.
        player_name_to_test = "TestPlayer_123" # <<<<<<< REPLACE THIS WITH A VALID KAKAO PLAYER NAME
        print(f"\n--- Testing get_player_id for player: {player_name_to_test} ---")
        account_id = pubg_service.get_player_id(player_name_to_test)
        if account_id:
            print(f"Player ID for {player_name_to_test}: {account_id}")

            # --- Test get_player_season_stats (only if account_id and test_season_id are valid) ---
            if test_season_id:
                print(f"\n--- Testing get_player_season_stats for account {account_id}, season {test_season_id} ---")
                season_stats_data = pubg_service.get_player_season_stats(account_id, test_season_id)
                if season_stats_data:
                    print(f"Successfully fetched season stats. Type: {season_stats_data.get('type')}")
                    game_mode_stats = season_stats_data.get('attributes', {}).get('gameModeStats', {})
                    if game_mode_stats:
                        print("Game Mode Stats (first mode found):")
                        for mode, stats in game_mode_stats.items():
                            print(f"  Mode: {mode}")
                            print(f"    Kills: {stats.get('kills', 0)}, Assists: {stats.get('assists', 0)}, Wins: {stats.get('wins', 0)}")
                            print(f"    Top10s: {stats.get('top10s', 0)}, Damage: {stats.get('damageDealt', 0):.2f}")
                            break # Just show one mode for brevity
                    else:
                        print("No gameModeStats found in attributes.")
                    
                    # Check for matches relationship (for get_player_matches Strategy 1)
                    if 'relationships' in season_stats_data and 'matches' in season_stats_data['relationships']:
                        print(f"Found 'matches' in relationships. Count: {len(season_stats_data['relationships']['matches'].get('data', []))}")
                    else:
                        print("'matches' not found in relationships of season stats.")
                else:
                    print(f"Could not get season stats for player {account_id} in season {test_season_id}.")

                # --- Test get_player_matches (depends on the above) ---
                print(f"\n--- Testing get_player_matches for account {account_id}, season {test_season_id} ---")
                match_ids_from_season = pubg_service.get_player_matches(account_id, test_season_id)
                if match_ids_from_season:
                    print(f"Found {len(match_ids_from_season)} match IDs from season stats. First few IDs: {match_ids_from_season[:5]}")
                    
                    # --- Test get_match_details (only if match_ids were found) ---
                    if match_ids_from_season:
                        test_match_id = match_ids_from_season[0] # Test with the first match ID
                        print(f"\n--- Testing get_match_details for match ID: {test_match_id} ---")
                        match_data = pubg_service.get_match_details(test_match_id)
                        if match_data:
                            print(f"Successfully fetched match details for {test_match_id}.")
                            print(f"  Match Type: {match_data.get('type')}, ID: {match_data.get('id')}")
                            match_attributes = match_data.get('attributes', {})
                            print(f"  Game Mode: {match_attributes.get('gameMode')}, Map: {match_attributes.get('mapName')}")
                            print(f"  Is Custom Match: {match_attributes.get('isCustomMatch')}, Duration: {match_attributes.get('duration')}s")
                            
                            # Participant info is in 'relationships' then needs to be looked up in 'included'
                            # For brevity, we'll just confirm if participant data is present.
                            if 'relationships' in match_data and 'rosters' in match_data['relationships']:
                                print(f"  Match contains roster data.")
                            
                            # The full match response also includes an 'included' array with participant/roster details
                            # included_data = data.get('included', []) # 'data' here is the raw response from _request
                            # if included_data:
                            #    print(f"  Match response includes {len(included_data)} items (participants, rosters, etc.).")

                        else:
                            print(f"Could not get details for match {test_match_id}.")
                else:
                    print(f"No match IDs returned by get_player_matches for season {test_season_id}.")
            else:
                print("\nSkipping player season stats, player matches, and match details tests because test_season_id is not set.")
        else:
            print(f"Could not get player ID for {player_name_to_test}. Skipping further tests that require account_id.")
            print("Please ensure 'player_name_to_test' is a valid Kakao PUBG player name.")

    print("\nPubgAPI local test examples finished.")
