import httpx
from .utils import limiter # Use relative import for utils
from .exceptions import (
    APIError, PlayerNotFoundAPIError, SeasonNotFoundAPIError, ClanNotFoundAPIError,
    MatchNotFoundAPIError, RateLimitErrorAPI, UnauthorizedErrorAPI, ForbiddenErrorAPI,
    ExternalAPIServiceError, BadRequestAPIError
)
from aiocache import cached # Import the cached decorator
from .cache_utils import default_key_builder # Import the custom key builder
import os # Import os to access environment variables

# API_KEY is now loaded from environment variable
PUBG_API_KEY = os.getenv("PUBG_API_KEY")

import logging # Use logging for better practice

# Check for API Key at module load time.
if not PUBG_API_KEY:
    # Log a critical message. The application will only fail hard if an API call is attempted without the key.
    logging.critical("CRITICAL: PUBG_API_KEY environment variable not set or empty. API calls will fail if attempted.")
    # DO NOT raise ValueError here to allow module import and decorator processing.

PUBG_API_BASE_URL = "https://api.pubg.com/shards/"

# _HEADERS is removed as get_headers() will construct headers dynamically

def get_headers():
    if not PUBG_API_KEY:
        # This will be the primary check if the module-level raise is commented out.
        raise UnauthorizedErrorAPI("PUBG API Key is not configured. Please set the PUBG_API_KEY environment variable.")
    return {
        "Authorization": f"Bearer {PUBG_API_KEY}",
        "Accept": "application/vnd.api+json",
    }

async def _make_request(url: str, identifier: str, platform: str, error_type: type[APIError], *args) -> dict:
    """Helper function to make HTTP requests and handle common errors."""
    try:
        async with limiter:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=get_headers())
                response.raise_for_status()
                return response.json()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 400:
            raise BadRequestAPIError(f"Bad request for {identifier} on {platform}: {e.response.text}") from e
        if status == 401:
            raise UnauthorizedErrorAPI(f"Unauthorized access for {identifier} on {platform}. Check API Key.") from e
        if status == 403:
            raise ForbiddenErrorAPI(f"Forbidden access for {identifier} on {platform}.") from e
        if status == 404:
            raise error_type(identifier, platform, *args) from e
        if status == 429:
            # aiolimiter should prevent this, but if it happens from PUBG's side directly to us.
            raise RateLimitErrorAPI(f"Rate limit exceeded for {identifier} on {platform}. Try again later.") from e
        if status >= 500:
            raise ExternalAPIServiceError(f"External API service error for {identifier} on {platform} ({status}): {e.response.text}", status_code=status) from e
        raise APIError(f"HTTP error {status} for {identifier} on {platform}: {e.response.text}", status_code=status) from e
    except httpx.RequestError as e: # Covers network errors, timeouts etc.
        raise ExternalAPIServiceError(f"Request error for {identifier} on {platform}: {str(e)}") from e
    except Exception as e: # Catch-all for unexpected issues
        raise APIError(f"An unexpected error occurred while fetching data for {identifier}: {str(e)}") from e

@cached(ttl=3600, key_builder=default_key_builder, cache="default") # TTL 1 hour
async def get_player_id(player_name: str, platform: str) -> dict:
    url = f"{PUBG_API_BASE_URL}{platform}/players?filter[playerNames]={player_name}"
    return await _make_request(url, player_name, platform, PlayerNotFoundAPIError)

@cached(ttl=1800, key_builder=default_key_builder, cache="default") # TTL 30 minutes
async def get_player_weapon_summaries(account_id: str, season_id: str, platform: str) -> dict:
    url = f"{PUBG_API_BASE_URL}{platform}/players/{account_id}/seasons/{season_id}/weapon_mastery"
    return await _make_request(url, account_id, platform, SeasonNotFoundAPIError, season_id)

@cached(ttl=120, key_builder=default_key_builder, cache="default") # TTL 2 minutes
async def get_player_match_history_ids(account_id: str, platform: str) -> list[str]:
    url = f"{PUBG_API_BASE_URL}{platform}/players/{account_id}"
    try:
        data = await _make_request(url, account_id, platform, PlayerNotFoundAPIError)
        match_ids = [
            match['id'] for match in data.get('data', {}).get('relationships', {}).get('matches', {}).get('data', [])
            if isinstance(match, dict) and 'id' in match
        ]
        return match_ids
    except (KeyError, TypeError) as e:
        raise APIError(f"Error parsing match IDs from player data for {account_id}: {str(e)}") from e

@cached(ttl=3600, key_builder=default_key_builder, cache="default") # TTL 1 hour
async def get_match_details(match_id: str, platform: str) -> dict:
    url = f"{PUBG_API_BASE_URL}{platform}/matches/{match_id}"
    return await _make_request(url, match_id, platform, MatchNotFoundAPIError)

@cached(ttl=1800, key_builder=default_key_builder, cache="default") # TTL 30 minutes
async def get_player_clan_details(account_id: str, platform: str) -> dict:
    player_clan_info_url = f"{PUBG_API_BASE_URL}{platform}/players/{account_id}/clan"
    clan_id = None
    try:
        player_clan_data = await _make_request(player_clan_info_url, account_id, platform, ClanNotFoundAPIError, True)
        if player_clan_data.get("data") and player_clan_data["data"].get("type") == "clan":
            clan_id = player_clan_data["data"].get("id")
        if not clan_id:
            raise ClanNotFoundAPIError(account_id, platform, by_player=True)
    except ClanNotFoundAPIError: 
         raise ClanNotFoundAPIError(account_id, platform, by_player=True)
    except PlayerNotFoundAPIError: 
         raise PlayerNotFoundAPIError(account_id, platform)

    clan_details_url = f"{PUBG_API_BASE_URL}{platform}/clans/{clan_id}"
    return await _make_request(clan_details_url, clan_id, platform, ClanNotFoundAPIError, False)

@cached(ttl=1800, key_builder=default_key_builder, cache="default") # TTL 30 minutes
async def get_player_seasonal_stats(account_id: str, season_id: str, platform: str) -> dict:
    url = f"{PUBG_API_BASE_URL}{platform}/players/{account_id}/seasons/{season_id}"
    return await _make_request(url, account_id, platform, SeasonNotFoundAPIError, season_id)
