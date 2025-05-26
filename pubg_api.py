import requests

# Custom Exceptions
class PlayerNotFoundException(Exception):
    """Custom exception for when a player is not found."""
    pass

class CurrentSeasonNotFoundException(Exception):
    """Custom exception for when the current season is not found."""
    pass

class SeasonStatsNotFoundException(Exception):
    """Custom exception for when player season stats are not found."""
    pass

class WeaponMasteryNotFoundException(Exception):
    """Custom exception for when player weapon mastery stats are not found."""
    pass

class ClanNotFoundException(Exception):
    """Custom exception for when a clan is not found."""
    pass

BASE_URL = "https://api.pubg.com/shards/"

def construct_api_url(platform):
    """Constructs the base API URL for the given platform."""
    return f"{BASE_URL}{platform}/"

def make_api_request(endpoint_url, api_key, params=None):
    """Makes a request to the PUBG API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
    }
    try:
        response = requests.get(endpoint_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle network errors or other request issues
        raise Exception(f"API request failed: {e}") # General exception for request failures

def get_player_id(platform, player_name, api_key):
    """
    Fetches the account ID for a given player name and platform.
    Raises PlayerNotFoundException if the player is not found.
    """
    endpoint_url = f"{construct_api_url(platform)}players"
    params = {"filter[playerNames]": player_name}
    
    try:
        response_json = make_api_request(endpoint_url, api_key, params)
    except Exception as e: # Catching exceptions from make_api_request
        raise Exception(f"Error fetching player data for {player_name}: {e}")

    if not response_json.get('data') or len(response_json['data']) == 0:
        raise PlayerNotFoundException(f"Player '{player_name}' not found on platform '{platform}'.")
    
    player_data_item = response_json['data'][0]
    account_id = player_data_item['id']
    attributes = player_data_item.get('attributes', {})
    validated_name = attributes.get('name', player_name) # Fallback to original name
    clan_id = attributes.get('clanId') # Will be None if not present
    
    return {"account_id": account_id, "name": validated_name, "clan_id": clan_id}

def get_current_season_id(platform, api_key):
    """
    Fetches the ID of the current season for a given platform.
    Raises CurrentSeasonNotFoundException if the current season is not found.
    """
    endpoint_url = f"{construct_api_url(platform)}seasons"
    
    try:
        response_json = make_api_request(endpoint_url, api_key)
    except Exception as e: # Catching exceptions from make_api_request
        raise Exception(f"Error fetching seasons data for {platform}: {e}")

    if not response_json.get('data'):
        raise CurrentSeasonNotFoundException(f"No season data found for platform '{platform}'.")

    for season in response_json['data']:
        if season.get('attributes', {}).get('isCurrentSeason'):
            return season['id']
            
    raise CurrentSeasonNotFoundException(f"No current season found for platform '{platform}'.")

def get_player_season_stats(platform, player_id, season_id, api_key):
    """
    Fetches the game mode stats for a player in a specific season.
    Raises SeasonStatsNotFoundException if the stats are not found.
    """
    endpoint_url = f"{construct_api_url(platform)}players/{player_id}/seasons/{season_id}"
    
    try:
        response_json = make_api_request(endpoint_url, api_key)
    except Exception as e: # Catching exceptions from make_api_request
        raise Exception(f"Error fetching player season stats for player {player_id}, season {season_id}: {e}")

    if not response_json.get('data'):
        raise SeasonStatsNotFoundException(f"No data found for player {player_id}, season {season_id}.")
    
    game_mode_stats = response_json['data'].get('attributes', {}).get('gameModeStats')
    
    if not game_mode_stats:
        # This case might mean the player simply hasn't played in that season/mode,
        # or the data structure is different than expected.
        # For now, we'll raise an exception if it's missing entirely.
        raise SeasonStatsNotFoundException(f"No gameModeStats found for player {player_id}, season {season_id}.")
        
    return game_mode_stats

def get_weapon_mastery_stats(platform, player_id, api_key):
    """
    Fetches the weapon mastery statistics for a player.
    Raises WeaponMasteryNotFoundException if the stats are not found.
    """
    endpoint_url = f"{construct_api_url(platform)}players/{player_id}/weapon_mastery"
    
    try:
        response_json = make_api_request(endpoint_url, api_key)
    except Exception as e: # Catching exceptions from make_api_request
        raise Exception(f"Error fetching weapon mastery stats for player {player_id}: {e}")

    if not response_json.get('data'):
        raise WeaponMasteryNotFoundException(f"No weapon mastery data found for player {player_id}.")
    
    weapon_summaries = response_json['data'].get('attributes', {}).get('weaponSummaries')
    
    if weapon_summaries is None: # It could be an empty dict {} if player has no mastery, which is valid
        raise WeaponMasteryNotFoundException(f"No weaponSummaries found for player {player_id}.")
        
    return weapon_summaries

def get_clan_info(platform, clan_id, api_key):
    """
    Fetches clan information including name, tag, and member account IDs.
    Raises ClanNotFoundException if the clan is not found.
    """
    endpoint_url = f"{construct_api_url(platform)}clans/{clan_id}"

    try:
        response_json = make_api_request(endpoint_url, api_key)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ClanNotFoundException(f"Clan with ID '{clan_id}' not found on platform '{platform}'.")
        raise Exception(f"API error fetching clan data for clan ID {clan_id}: {e}")
    except Exception as e: # Catching other exceptions from make_api_request
        raise Exception(f"Error fetching clan data for clan ID {clan_id}: {e}")

    if not response_json.get('data') or not response_json['data'].get('attributes'):
        # This case might indicate an unexpected response structure even if not a 404
        raise ClanNotFoundException(f"Clan data for ID '{clan_id}' is incomplete or malformed.")

    clan_attributes = response_json['data']['attributes']
    clan_name = clan_attributes.get('clanName', 'N/A')
    clan_tag = clan_attributes.get('clanTag', 'N/A')
    
    members_list = []
    # The relationships object seems to be the standard way PUBG API represents this
    # Example structure: response_json['data']['relationships']['members']['data']
    # Each item in 'data' list is like: {'type': 'player', 'id': 'account.xxxx'}
    relationships = response_json['data'].get('relationships', {})
    members_data = relationships.get('members', {}).get('data', [])

    for member_item in members_data:
        if member_item.get('type') == 'player' and 'id' in member_item:
            members_list.append({"account_id": member_item['id']}) 
            # Name is not usually available in this part of the API response for clan members.
            # If it were, it would be member_item.get('attributes', {}).get('name') but that's unlikely here.

    return {
        "clan_id": clan_id, # Good to return the ID for confirmation
        "clan_name": clan_name,
        "clan_tag": clan_tag,
        "members": members_list
    }
