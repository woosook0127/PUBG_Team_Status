import json
from pubg_api import make_api_request, construct_api_url

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ZGRmZjNhMC0xOWE4LTAxM2UtNWQ1YS0wMmE4MzJlYWU5ZTEiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzQ3OTY1OTQ3LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1hY2QxZWU4ZS01ZmNmLTQ2ODgtOTEwYy0xOTE4Y2Y3OTUwNWIifQ.WsX8ac86_fKIjDQwIsvpa_5UOadW322uI3Pl5HeAci4"
PLATFORM = "steam"
PLAYER_NAME = "chocoTaco"

def save_json_to_file(data, filename):
    """Saves JSON data to a file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

def main():
    # 1. Get Player Account ID
    player_id = None
    try:
        print(f"Fetching player ID for {PLAYER_NAME} on {PLATFORM}...")
        player_url = f"{construct_api_url(PLATFORM)}players"
        player_params = {"filter[playerNames]": PLAYER_NAME}
        player_data = make_api_request(player_url, API_KEY, player_params)
        save_json_to_file(player_data, f"player_{PLAYER_NAME}_{PLATFORM}.json")
        if player_data and 'data' in player_data and len(player_data['data']) > 0:
            player_id = player_data['data'][0]['id']
            print(f"Player ID for {PLAYER_NAME}: {player_id}")
        else:
            print(f"Could not find player ID for {PLAYER_NAME}")
            return # Exit if no player ID
    except Exception as e:
        print(f"Error fetching player ID: {e}")
        return # Exit on error

    # 2. Get Seasons List
    season_id = None
    try:
        print(f"Fetching seasons list for {PLATFORM}...")
        seasons_url = f"{construct_api_url(PLATFORM)}seasons"
        seasons_data = make_api_request(seasons_url, API_KEY)
        save_json_to_file(seasons_data, f"seasons_{PLATFORM}.json")
        if seasons_data and 'data' in seasons_data:
            # Find current season
            for season in seasons_data['data']:
                if season.get('attributes', {}).get('isCurrentSeason'):
                    season_id = season['id']
                    print(f"Current season ID: {season_id}")
                    break
            if not season_id and len(seasons_data['data']) > 0: # If no current season, pick the last one
                season_id = seasons_data['data'][-1]['id']
                print(f"Using latest season ID (no current season found): {season_id}")
            elif not season_id:
                 print("No seasons found.")
                 return # Exit if no season ID
        else:
            print("Could not fetch seasons data.")
            return # Exit if no seasons data
    except Exception as e:
        print(f"Error fetching seasons: {e}")
        return # Exit on error

    # 3. Get Player Season Stats
    if player_id and season_id:
        try:
            print(f"Fetching season stats for player {player_id}, season {season_id} on {PLATFORM}...")
            season_stats_url = f"{construct_api_url(PLATFORM)}players/{player_id}/seasons/{season_id}"
            season_stats_data = make_api_request(season_stats_url, API_KEY)
            save_json_to_file(season_stats_data, f"player_season_stats_{PLAYER_NAME}_{PLATFORM}.json")
        except Exception as e:
            print(f"Error fetching player season stats: {e}")
    else:
        print("Skipping player season stats due to missing player ID or season ID.")

    # 4. Get Player Weapon Mastery Stats
    if player_id:
        try:
            print(f"Fetching weapon mastery for player {player_id} on {PLATFORM}...")
            weapon_mastery_url = f"{construct_api_url(PLATFORM)}players/{player_id}/weapon_mastery"
            weapon_mastery_data = make_api_request(weapon_mastery_url, API_KEY)
            save_json_to_file(weapon_mastery_data, f"player_weapon_mastery_{PLAYER_NAME}_{PLATFORM}.json")
        except Exception as e:
            print(f"Error fetching weapon mastery: {e}")
    else:
        print("Skipping weapon mastery stats due to missing player ID.")

if __name__ == "__main__":
    main()
