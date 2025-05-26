from flask import Flask, jsonify, request
from pubg_api import (
    make_api_request, 
    construct_api_url, 
    get_player_id, 
    get_current_season_id, 
    get_player_season_stats,
    get_weapon_mastery_stats, # Added
    PlayerNotFoundException, 
    CurrentSeasonNotFoundException,
    SeasonStatsNotFoundException,
    WeaponMasteryNotFoundException,
    ClanNotFoundException # Added
)
from weapon_utils import get_top_damage_weapons_by_category

app = Flask(__name__)

# Placeholder for database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pubg_stats.db'  # Example URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Replace with your actual API key
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ZGRmZjNhMC0xOWE4LTAxM2UtNWQ1YS0wMmE4MzJlYWU5ZTEiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzQ3OTY1OTQ3LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1hY2QxZWU4ZS01ZmNmLTQ2ODgtOTEwYy0xOTE4Y2Y3OTUwNWIifQ.WsX8ac86_fKIjDQwIsvpa_5UOadW322uI3Pl5HeAci4" # Replace with your actual API key

@app.route('/player_info/<platform>/<player_name>')
def get_player_info(platform, player_name):
    """
    Fetches player account ID and current season ID using the new functions.
    """
    try:
        player_account_id = get_player_id(platform, player_name, API_KEY)
        current_season_id = get_current_season_id(platform, API_KEY)
        
        return jsonify({
            "playerName": player_name,
            "platform": platform,
            "accountId": player_account_id,
            "currentSeasonId": current_season_id
        })
        
    except PlayerNotFoundException as e:
        return jsonify({"error": str(e), "details": "Player not found on the specified platform."}), 404
    except CurrentSeasonNotFoundException as e:
        return jsonify({"error": str(e), "details": "Current season ID could not be determined."}), 404
    except Exception as e:
        # This will catch general exceptions from make_api_request or other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/raw_player_season_stats/<platform>/<player_name>')
def get_raw_player_season_stats(platform, player_name):
    """
    Fetches the raw gameModeStats for a player for the current season.
    """
    try:
        player_id = get_player_id(platform, player_name, API_KEY)
        season_id = get_current_season_id(platform, API_KEY)
        
        season_stats = get_player_season_stats(platform, player_id, season_id, API_KEY)
        
        return jsonify(season_stats)
        
    except PlayerNotFoundException as e:
        return jsonify({"error": str(e), "details": f"Player '{player_name}' not found on platform '{platform}'."}), 404
    except CurrentSeasonNotFoundException as e:
        return jsonify({"error": str(e), "details": f"Current season not found for platform '{platform}'."}), 404
    except SeasonStatsNotFoundException as e:
        # This could mean the player hasn't played in the current season, or no stats are available.
        return jsonify({"error": str(e), "details": f"Season stats not found for player '{player_name}' in the current season on platform '{platform}'. This might mean the player has not played in this season."}), 404
    except Exception as e: # Catch-all for other errors, like API request failures in get_player_season_stats
        return jsonify({"error": f"An unexpected error occurred while fetching season stats: {str(e)}"}), 500

@app.route('/player_top_weapons/<platform>/<player_name>')
def player_top_weapons(platform, player_name):
    """
    Fetches and processes weapon mastery stats to return top damage weapons by category.
    """
    try:
        player_id = get_player_id(platform, player_name, API_KEY)
        
        weapon_summaries = get_weapon_mastery_stats(platform, player_id, API_KEY)
        # get_weapon_mastery_stats returns {} if 'weaponSummaries' is missing or player has no mastery,
        # or raises WeaponMasteryNotFoundException if the entire 'data' object for mastery is missing.
        
        top_weapons_by_category = get_top_damage_weapons_by_category(weapon_summaries)
        
        return jsonify({
            "playerName": player_name,
            "platform": platform,
            "topWeaponsByCategory": top_weapons_by_category
        })

    except PlayerNotFoundException as e:
        return jsonify({"error": str(e), "details": f"Player '{player_name}' not found on platform '{platform}'."}), 404
    except WeaponMasteryNotFoundException as e:
        # This implies the API didn't return a 'data' object for weapon mastery at all.
        return jsonify({"error": str(e), "details": f"Weapon mastery data not found for player '{player_name}' on platform '{platform}'. The player might exist but have no weapon mastery data available."}), 404
    except Exception as e: # Catch-all for other errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/player_summary/<platform>/<player_name_input>')
def player_summary(platform, player_name_input):
    """
    Provides a consolidated summary of a player's information, current season stats,
    and top weapons by category.
    """
    try:
        # 1. Get Player ID and Validated Name
        player_data = get_player_id(platform, player_name_input, API_KEY)
        player_id = player_data["account_id"]
        validated_player_name = player_data["name"]

        # 2. Get Current Season ID
        current_season_id = get_current_season_id(platform, API_KEY)

        # 3. Get Player Season Stats for the current season
        # Initialize to None or empty dict in case of SeasonStatsNotFoundException
        game_mode_stats = {} 
        try:
            game_mode_stats = get_player_season_stats(platform, player_id, current_season_id, API_KEY)
        except SeasonStatsNotFoundException:
            # Player might not have played in the current season, this is not a fatal error for the summary
            game_mode_stats = {"message": f"No season stats found for player {validated_player_name} in season {current_season_id}. They may not have played in this season."}


        # 4. Get Top Weapons by Category
        # Initialize to None or empty dict in case of WeaponMasteryNotFoundException
        top_weapons_by_category = {}
        try:
            weapon_summaries = get_weapon_mastery_stats(platform, player_id, API_KEY)
            top_weapons_by_category = get_top_damage_weapons_by_category(weapon_summaries)
        except WeaponMasteryNotFoundException:
            # Player might not have weapon mastery data, not a fatal error for summary
            top_weapons_by_category = {"message": f"No weapon mastery data found for player {validated_player_name}."}
        
        # 5. Construct the summary response
        summary_response = {
            "player_info": {
                "account_id": player_id,
                "name": validated_player_name, # Using validated name
                "platform": platform,
                "requested_name": player_name_input 
            },
            "current_season_id": current_season_id,
            "season_stats": game_mode_stats,
            "weapon_summary": top_weapons_by_category
        }
        return jsonify(summary_response)

    except PlayerNotFoundException as e:
        return jsonify({"error": str(e), "details": f"Player '{player_name_input}' not found on platform '{platform}'."}), 404
    except CurrentSeasonNotFoundException as e:
        # This is more critical as other calls depend on it for "current" stats
        return jsonify({"error": str(e), "details": f"Current season not found for platform '{platform}'. Cannot retrieve full summary."}), 500
    except Exception as e: # Catch-all for other unexpected errors (e.g. API rate limits, general request failures)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/player_clan_details/<platform>/<player_name_input>')
def player_clan_details(platform, player_name_input):
    """
    Fetches clan details for a given player if they are in a clan.
    """
    try:
        player_data = get_player_id(platform, player_name_input, API_KEY)
        player_id = player_data["account_id"] # Used for potential future use, not directly for clan info here
        validated_player_name = player_data["name"]
        clan_id = player_data.get("clan_id")

        if not clan_id:
            return jsonify({
                "player_name": validated_player_name,
                "message": "Player is not currently in a clan."
            }), 200 # 200 is fine as it's not an error, just info

        # If clan_id exists, fetch clan details
        clan_info = get_clan_info(platform, clan_id, API_KEY)
        
        return jsonify({
            "player_name": validated_player_name, # Add player name for context
            "clan_details": clan_info
        })

    except PlayerNotFoundException as e:
        return jsonify({"error": str(e), "details": f"Player '{player_name_input}' not found on platform '{platform}'."}), 404
    except ClanNotFoundException as e:
        # This means the clan_id obtained from player data was invalid or clan disbanded etc.
        return jsonify({"error": str(e), "details": f"Clan details could not be fetched for clan ID '{clan_id}' associated with player '{validated_player_name}'. The clan may no longer exist or the ID is invalid."}), 404
    except Exception as e: # Catch-all for other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Example of the original route if you want to keep it or modify it
# For now, I'll comment it out to avoid confusion with the new route.
# @app.route('/player_stats/<platform>/<player_name>')
# def get_player_stats(platform, player_name):
#     """
#     Fetches player stats from the PUBG API.
#     """
#     try:
#         base_url = construct_api_url(platform)
#         # This endpoint might need to be more specific, e.g., lifetime stats or season stats
#         # For season stats, you'd use: /players/{accountId}/seasons/{seasonId}
#         # For lifetime stats: /players/{accountId}/seasons/lifetime
#         # The original logic was just fetching player account details, not really "stats"
#         endpoint_url = f"{base_url}players" 
#         params = {
#             "filter[playerNames]": player_name,
#         }
#         data = make_api_request(endpoint_url, API_KEY, params)
#         return jsonify(data)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
