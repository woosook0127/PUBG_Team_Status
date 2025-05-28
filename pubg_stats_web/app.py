import os
import logging
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Service and Helper Imports ---
try:
    from services.pubg_api import PubgAPI
    from utils.helpers import (
        calculate_individual_player_stats,
        identify_frequent_teammates,
        calculate_teammate_synergy_stats,
        calculate_individual_weapon_stats
        # format_player_stats_for_display, # Not directly used in API routes, but good to have if needed later
        # prepare_chart_data # Not directly used in API routes
    )
except ImportError as e:
    logging.error(f"Error importing modules: {e}. Ensure services and utils are in PYTHONPATH.")
    # Exit or raise if critical modules are missing, for now, we'll let Flask fail if they are truly gone.
    PubgAPI = None # Will cause errors later if not resolved, good for debugging path issues
    # Define placeholders if needed for Flask to start, though routes will fail
    calculate_individual_player_stats = lambda x: {}
    identify_frequent_teammates = lambda a,b,c,d=5: {}
    calculate_teammate_synergy_stats = lambda a,b,c: {}
    calculate_individual_weapon_stats = lambda a,b,c: {}


app = Flask(__name__)

# --- Logging Configuration ---
# Basic logging (can be expanded)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
app.logger.setLevel(logging.INFO) # Use Flask's logger for app-specific logs

# --- Environment Variable & API Key ---
PUBG_API_KEY = os.getenv("PUBG_API_KEY")

if not PUBG_API_KEY:
    app.logger.warning("PUBG_API_KEY not found in environment variables. API calls will fail.")
    # For critical missing config, you might choose to exit:
    # raise RuntimeError("PUBG_API_KEY not configured. Application cannot start.")


# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/seasons', methods=['GET'])
def get_seasons_route():
    app.logger.info("Received request for /api/seasons")
    if not PUBG_API_KEY:
        app.logger.error("API Key not configured for /api/seasons.")
        return jsonify({"error": "API Key not configured on server."}), 500
    if PubgAPI is None: # Check if import failed
        app.logger.error("PubgAPI service not available due to import error.")
        return jsonify({"error": "Internal server error: API service unavailable."}), 500

    try:
        pubg_api_service = PubgAPI(api_key=PUBG_API_KEY) # Kakao is default platform
        seasons_data = pubg_api_service.get_seasons() 

        # PubgAPI.get_seasons() returns a list of season objects, or an empty list on error/no data.
        # The service method itself logs detailed errors.
        if not seasons_data: # Could be an error or simply no seasons found
             app.logger.warning("PubgAPI.get_seasons returned an empty list. This could be due to an API error (check service logs) or no seasons being available.")
             # Return empty list to frontend; frontend can decide how to interpret
             # (e.g., "No seasons available" vs. "Error loading seasons" if other indicators suggest error)
             # For now, returning empty list is consistent with "no data available".
             # If we wanted to be more specific about errors, PubgAPI methods would need to throw exceptions
             # or return a more complex object indicating error type.
             return jsonify({'data': []}) # Return empty list if service indicates error by returning empty

        app.logger.info(f"Successfully fetched {len(seasons_data)} seasons.")
        return jsonify({'data': seasons_data})

    except Exception as e:
        app.logger.error(f"Unexpected error in /api/seasons: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred."}), 500


@app.route('/api/player_stats', methods=['GET'])
def get_player_stats_route():
    app.logger.info("Received request for /api/player_stats")
    if not PUBG_API_KEY:
        app.logger.error("API Key not configured for /api/player_stats.")
        return jsonify({"error": "API Key not configured on server."}), 500
    if PubgAPI is None:
        app.logger.error("PubgAPI service not available.")
        return jsonify({"error": "Internal server error: API service unavailable."}), 500

    player_name = request.args.get('playerName')
    season_id = request.args.get('seasonId')
    game_type = request.args.get('gameType', 'ranked')  # Default to 'ranked'
    perspective = request.args.get('perspective', 'tpp') # Default to 'tpp'

    if not player_name:
        app.logger.warning("Missing playerName parameter.")
        return jsonify({"error": "playerName parameter is required."}), 400
    if not season_id:
        app.logger.warning("Missing seasonId parameter.")
        return jsonify({"error": "seasonId parameter is required."}), 400

    app.logger.info(f"Processing stats for player: {player_name}, season: {season_id}")

    try:
        pubg_api_service = PubgAPI(api_key=PUBG_API_KEY)

        # 1. Fetch Player Account ID
        account_id = pubg_api_service.get_player_id(player_name)
        if account_id is None:
            # PubgAPI.get_player_id logs specific errors (e.g., 404 Not Found, API error)
            app.logger.warning(f"Player not found or error fetching ID for: {player_name}")
            return jsonify({"error": f"Player '{player_name}' not found or an API error occurred."}), 404
        app.logger.info(f"Player ID for {player_name}: {account_id}")

        # Construct game_mode_filter
        # Assuming "squad" is the team size for now.
        # Default to "ranked-squad" (Ranked TPP Squad) if parameters are missing,
        # aligning with user's default preference.
        if game_type == "ranked":
            if perspective == "fpp":
                game_mode_filter = "ranked-squad-fpp"
            else: # Default to tpp for ranked
                game_mode_filter = "ranked-squad"
        else: # game_type is "normal" or something else (default to normal logic)
            if perspective == "fpp":
                game_mode_filter = "squad-fpp"
            else: # Default to tpp for normal
                game_mode_filter = "squad"
        
        app.logger.info(f"Constructed game mode filter: {game_mode_filter} (gameType: {game_type}, perspective: {perspective})")

        # 2. Fetch Player Season Stats (Overall, now with game mode filter)
        player_season_data = pubg_api_service.get_player_season_stats(
            account_id, 
            season_id, 
            game_mode_filter=game_mode_filter
        )
        if player_season_data is None:
            # PubgAPI.get_player_season_stats logs specific errors
            app.logger.error(f"Could not fetch season stats for account {account_id}, season {season_id}, filter {game_mode_filter}.")
            return jsonify({"error": "Could not fetch season stats for this player. The account may be invalid or there's no data for the selected season/game mode."}), 404 # Or 500 if server-side API issue
        app.logger.info(f"Fetched season stats for {account_id} with filter {game_mode_filter}")
        
        # 3. Calculate Individual Stats
        individual_stats = calculate_individual_player_stats(player_season_data)
        app.logger.info(f"Calculated individual stats: {individual_stats is not None}")

        # 4. Identify Frequent Teammates
        frequent_teammates_data = identify_frequent_teammates(pubg_api_service, account_id, season_id)
        app.logger.info(f"Identified {len(frequent_teammates_data)} frequent teammates.")

        # 5. Calculate Synergy Stats for Teammates
        processed_teammates = []
        if frequent_teammates_data:
            for tm_account_id, tm_data in frequent_teammates_data.items():
                synergy_stats = calculate_teammate_synergy_stats(
                    pubg_api_service, 
                    tm_data.get('matchIds', []), 
                    tm_account_id
                )
                processed_teammates.append({
                    'accountId': tm_account_id,
                    'playerName': tm_data.get('playerName', 'N/A'),
                    'matchesTogether': tm_data.get('matchesTogether', 0),
                    'synergyStats': synergy_stats if synergy_stats else {}
                })
        app.logger.info(f"Processed synergy for {len(processed_teammates)} teammates.")

        # 6. Calculate Weapon Stats (Placeholder)
        # PubgAPI.get_player_matches returns a list of match_ids or an empty list on error/no data.
        season_match_ids_for_weapons = pubg_api_service.get_player_matches(account_id, season_id)
        if not season_match_ids_for_weapons: # Check if list is empty
             app.logger.warning(f"No match IDs found for player {account_id}, season {season_id} by get_player_matches. Weapon stats might be empty or based on no matches.")
        
        weapon_stats = calculate_individual_weapon_stats(
            pubg_api_service, 
            account_id, 
            season_match_ids_for_weapons # Pass potentially empty list
        )
        app.logger.info(f"Calculated weapon stats (placeholder: {weapon_stats is not None})")

        # 7. Fetch Match Logs (Sample)
        match_logs = []
        # Re-use season_match_ids_for_weapons, which is the list of all matches for the player in that season
        sample_match_ids = season_match_ids_for_weapons[:5] # Sample of first 5 matches
        app.logger.info(f"Fetching details for {len(sample_match_ids)} sample matches for logs.")

        for match_id_log in sample_match_ids:
            full_match_details = pubg_api_service.get_match_details(match_id_log)
            if full_match_details is None: # Indicates error logged by PubgAPI
                app.logger.warning(f"Could not get details for match log {match_id_log}. Skipping.")
                continue
            # 'data' might be missing if full_match_details is None, but we check None above.
            # However, if get_match_details returns a dict that's not None but malformed (e.g. no 'data'), we add a check.
            if 'data' not in full_match_details:
                 app.logger.warning(f"Incomplete match details (missing 'data' field) for match log {match_id_log}. Skipping.")
                 continue

            player_kills_in_match = 0
            player_damage_in_match = 0.0
            team_rank = None
            
            game_mode = full_match_details.get('data', {}).get('attributes', {}).get('gameMode', 'N/A')
            included_data = full_match_details.get('included', []) # Might be empty, that's fine
            
            player_participant_obj = None
            for item in included_data: # Iterate safely
                if item.get('type') == 'participant' and item.get('attributes', {}).get('stats', {}).get('playerId') == account_id:
                    player_participant_obj = item
                    p_stats = player_participant_obj.get('attributes', {}).get('stats', {})
                    player_kills_in_match = p_stats.get('kills', 0)
                    player_damage_in_match = p_stats.get('damageDealt', 0.0)
                    break
            
            if player_participant_obj:
                for item in included_data:
                    if item.get('type') == 'roster':
                        roster_participants_refs = item.get('relationships', {}).get('participants', {}).get('data', [])
                        for ref in roster_participants_refs:
                            if ref.get('id') == player_participant_obj.get('id'): # participant's API ID, not account_id
                                team_rank = item.get('attributes', {}).get('stats', {}).get('rank')
                                break
                        if team_rank is not None:
                            break
            
            match_logs.append({
                'id': match_id_log,
                'gameMode': game_mode,
                'rank': team_rank if team_rank is not None else 'N/A',
                'kills': player_kills_in_match,
                'damageDealt': round(player_damage_in_match, 2)
            })
        app.logger.info(f"Processed {len(match_logs)} match logs.")

        # 8. Construct Final JSON Response
        response_data = {
            "playerName": player_name, # Or a name from API if available and preferred
            "accountId": account_id,
            "seasonId": season_id,
            "individualStats": individual_stats if individual_stats else {},
            "frequentTeammates": processed_teammates,
            "weaponStats": weapon_stats if weapon_stats else {},
            "matchLogs": match_logs
        }
        app.logger.info(f"Successfully compiled all stats for player {player_name}, season {season_id}.")
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Unexpected error in /api/player_stats for {player_name}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred while fetching player stats."}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # Check if the script is run with Flask's reloader, to avoid double printing the warning.
    # Or more simply, just print it once.
    if not PUBG_API_KEY and not os.environ.get("WERKZEUG_RUN_MAIN"):
        print("Reminder: PUBG_API_KEY is not set. API calls will fail.")
        print("Please create a .env file in the pubg_stats_web directory with your API key:")
        print("Example .env file content:")
        print("PUBG_API_KEY=your_actual_api_key_here")
    
    app.run(debug=True)
