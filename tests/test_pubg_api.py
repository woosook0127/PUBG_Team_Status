import pytest
import httpx # For creating mock response objects
from unittest.mock import AsyncMock, patch # For async mocking

from app import pubg_api # The module to test
from app.exceptions import (
    PlayerNotFoundAPIError, SeasonNotFoundAPIError, ClanNotFoundAPIError,
    MatchNotFoundAPIError, RateLimitErrorAPI, UnauthorizedErrorAPI, 
    ForbiddenErrorAPI, ExternalAPIServiceError, BadRequestAPIError, APIError
)
from app.cache_utils import default_cache # For cache testing

# Sample data for mocking
SAMPLE_PLAYER_NAME = "test_player"
SAMPLE_ACCOUNT_ID = "account.testplayer123"
SAMPLE_PLATFORM = "steam"
SAMPLE_SEASON_ID = "division.bro.official.pc-2018-01"
SAMPLE_MATCH_ID = "matchid12345"
SAMPLE_CLAN_ID = "clanidABCDE"

# Default headers for mock responses
JSON_CONTENT_TYPE = {"Content-Type": "application/vnd.api+json"}


@pytest.fixture(autouse=True)
async def clear_cache_before_each_test():
    """Fixture to automatically clear the cache before each test."""
    await default_cache.delete(default_cache.namespace) # Clears all keys in the 'default' cache namespace
    # If using multiple cache instances or specific keys, clear them accordingly.

@pytest.fixture
def mock_httpx_client(mocker):
    """Fixture to mock httpx.AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    # The __aenter__ and __aexit__ methods are part of the async context manager protocol
    mock_client.__aenter__.return_value = mock_client 
    mock_client.__aexit__.return_value = None # Or AsyncMock() if it needs to be awaitable and return something
    
    # Patch httpx.AsyncClient to return this mock_client
    # This ensures that when 'async with httpx.AsyncClient() as client:' is called in pubg_api.py,
    # our mock_client is used.
    mocker.patch('httpx.AsyncClient', return_value=mock_client)
    return mock_client


# --- Tests for get_player_id ---
@pytest.mark.asyncio
async def test_get_player_id_success(mock_httpx_client):
    mock_response_data = {"data": [{"id": SAMPLE_ACCOUNT_ID, "type": "player"}]}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)

    result = await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    
    assert result == mock_response_data
    expected_url = f"{pubg_api.PUBG_API_BASE_URL}{SAMPLE_PLATFORM}/players?filter[playerNames]={SAMPLE_PLAYER_NAME}"
    mock_httpx_client.get.assert_called_once_with(expected_url, headers=pubg_api.get_headers())

@pytest.mark.asyncio
async def test_get_player_id_not_found(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    
    with pytest.raises(PlayerNotFoundAPIError) as excinfo:
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    assert SAMPLE_PLAYER_NAME in str(excinfo.value)
    assert SAMPLE_PLATFORM in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_player_id_rate_limit(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(429, json={"errors": [{"title": "Too Many Requests"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(RateLimitErrorAPI):
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)

@pytest.mark.asyncio
async def test_get_player_id_unauthorized(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(401, json={"errors": [{"title": "Unauthorized"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(UnauthorizedErrorAPI):
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)

@pytest.mark.asyncio
async def test_get_player_id_forbidden(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(403, json={"errors": [{"title": "Forbidden"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(ForbiddenErrorAPI):
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)

@pytest.mark.asyncio
async def test_get_player_id_server_error(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(500, json={"errors": [{"title": "Internal Server Error"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(ExternalAPIServiceError):
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)

@pytest.mark.asyncio
async def test_get_player_id_request_error(mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.RequestError("Network error", request=httpx.Request('GET', ''))
    with pytest.raises(ExternalAPIServiceError) as excinfo:
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    assert "Request error" in str(excinfo.value)


# --- Tests for get_player_seasonal_stats ---
@pytest.mark.asyncio
async def test_get_player_seasonal_stats_success(mock_httpx_client):
    mock_response_data = {"data": {"type": "playerSeason", "attributes": {"gameModeStats": {}}}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    
    result = await pubg_api.get_player_seasonal_stats(SAMPLE_ACCOUNT_ID, SAMPLE_SEASON_ID, SAMPLE_PLATFORM)
    assert result == mock_response_data
    expected_url = f"{pubg_api.PUBG_API_BASE_URL}{SAMPLE_PLATFORM}/players/{SAMPLE_ACCOUNT_ID}/seasons/{SAMPLE_SEASON_ID}"
    mock_httpx_client.get.assert_called_once_with(expected_url, headers=pubg_api.get_headers())

@pytest.mark.asyncio
async def test_get_player_seasonal_stats_not_found(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(SeasonNotFoundAPIError) as excinfo:
        await pubg_api.get_player_seasonal_stats(SAMPLE_ACCOUNT_ID, SAMPLE_SEASON_ID, SAMPLE_PLATFORM)
    assert SAMPLE_SEASON_ID in str(excinfo.value)
    assert SAMPLE_ACCOUNT_ID in str(excinfo.value)


# --- Tests for get_player_weapon_summaries ---
@pytest.mark.asyncio
async def test_get_player_weapon_summaries_success(mock_httpx_client):
    mock_response_data = {"data": {"type": "weaponSummaries", "attributes": {"weaponSummaries": {}}}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    
    result = await pubg_api.get_player_weapon_summaries(SAMPLE_ACCOUNT_ID, SAMPLE_SEASON_ID, SAMPLE_PLATFORM)
    assert result == mock_response_data
    expected_url = f"{pubg_api.PUBG_API_BASE_URL}{SAMPLE_PLATFORM}/players/{SAMPLE_ACCOUNT_ID}/seasons/{SAMPLE_SEASON_ID}/weapon_mastery"
    mock_httpx_client.get.assert_called_once_with(expected_url, headers=pubg_api.get_headers())

@pytest.mark.asyncio
async def test_get_player_weapon_summaries_not_found(mock_httpx_client):
    # This endpoint uses SeasonNotFoundAPIError if the season/player combination isn't found
    mock_httpx_client.get.return_value = httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(SeasonNotFoundAPIError) as excinfo: # Or potentially PlayerNotFound if that's how API behaves
        await pubg_api.get_player_weapon_summaries(SAMPLE_ACCOUNT_ID, SAMPLE_SEASON_ID, SAMPLE_PLATFORM)
    assert SAMPLE_SEASON_ID in str(excinfo.value)


# --- Tests for get_player_match_history_ids ---
@pytest.mark.asyncio
async def test_get_player_match_history_ids_success(mock_httpx_client):
    mock_response_data = {
        "data": {
            "type": "player", 
            "id": SAMPLE_ACCOUNT_ID,
            "relationships": {
                "matches": {
                    "data": [
                        {"type": "match", "id": "match1"},
                        {"type": "match", "id": "match2"}
                    ]
                }
            }
        }
    }
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    result = await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert result == ["match1", "match2"]

@pytest.mark.asyncio
async def test_get_player_match_history_ids_no_matches(mock_httpx_client):
    mock_response_data = {"data": {"type": "player", "id": SAMPLE_ACCOUNT_ID, "relationships": {"matches": {"data": []}}}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    result = await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert result == []

@pytest.mark.asyncio
async def test_get_player_match_history_ids_malformed_response(mock_httpx_client):
    mock_response_data = {"data": {"type": "player", "id": SAMPLE_ACCOUNT_ID, "relationships": {"no_matches_key": {}}}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    # Expect an empty list because the path to matches is not found, not an error.
    # The function's parsing logic handles this by returning empty list.
    # If strict parsing error is desired, the function needs to change.
    # Current behavior:
    result = await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert result == [] 
    # If we wanted to raise an APIError for malformed data:
    # with pytest.raises(APIError) as excinfo:
    #     await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    # assert "Error parsing match IDs" in str(excinfo.value)


# --- Tests for get_match_details ---
@pytest.mark.asyncio
async def test_get_match_details_success(mock_httpx_client):
    mock_response_data = {"data": {"type": "match", "id": SAMPLE_MATCH_ID}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)
    result = await pubg_api.get_match_details(SAMPLE_MATCH_ID, SAMPLE_PLATFORM)
    assert result == mock_response_data

@pytest.mark.asyncio
async def test_get_match_details_not_found(mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    with pytest.raises(MatchNotFoundAPIError):
        await pubg_api.get_match_details(SAMPLE_MATCH_ID, SAMPLE_PLATFORM)


# --- Tests for get_player_clan_details ---
@pytest.mark.asyncio
async def test_get_player_clan_details_success(mock_httpx_client):
    # Step 1: Mock response for /players/{id}/clan
    mock_player_clan_response = {"data": {"type": "clan", "id": SAMPLE_CLAN_ID}}
    # Step 2: Mock response for /clans/{clanId}
    mock_clan_details_response = {"data": {"type": "clan", "id": SAMPLE_CLAN_ID, "attributes": {"name": "Test Clan"}}}

    # Set up side_effect to return different responses for different calls
    mock_httpx_client.get.side_effect = [
        httpx.Response(200, json=mock_player_clan_response, headers=JSON_CONTENT_TYPE),
        httpx.Response(200, json=mock_clan_details_response, headers=JSON_CONTENT_TYPE)
    ]
    
    result = await pubg_api.get_player_clan_details(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert result == mock_clan_details_response
    
    assert mock_httpx_client.get.call_count == 2
    calls = mock_httpx_client.get.call_args_list
    assert calls[0][0][0] == f"{pubg_api.PUBG_API_BASE_URL}{SAMPLE_PLATFORM}/players/{SAMPLE_ACCOUNT_ID}/clan"
    assert calls[1][0][0] == f"{pubg_api.PUBG_API_BASE_URL}{SAMPLE_PLATFORM}/clans/{SAMPLE_CLAN_ID}"

@pytest.mark.asyncio
async def test_get_player_clan_details_player_not_in_clan(mock_httpx_client):
    # /players/{id}/clan returns 404
    mock_httpx_client.get.return_value = httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    
    with pytest.raises(ClanNotFoundAPIError) as excinfo:
        await pubg_api.get_player_clan_details(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert "not found for player" in str(excinfo.value).lower() # by_player=True message

@pytest.mark.asyncio
async def test_get_player_clan_details_clan_id_not_found_after_player_clan_call(mock_httpx_client):
    # /players/{id}/clan returns 200 but malformed/no clan ID
    mock_player_clan_response = {"data": {"type": "NotAClanObject"}} # No ID
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_player_clan_response, headers=JSON_CONTENT_TYPE)
    
    with pytest.raises(ClanNotFoundAPIError) as excinfo:
        await pubg_api.get_player_clan_details(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert "not found for player" in str(excinfo.value).lower() # Should indicate player has no valid clan link

@pytest.mark.asyncio
async def test_get_player_clan_details_actual_clan_not_found(mock_httpx_client):
    # Step 1: /players/{id}/clan returns valid clan ID
    mock_player_clan_response = {"data": {"type": "clan", "id": SAMPLE_CLAN_ID}}
    # Step 2: /clans/{clanId} returns 404
    mock_httpx_client.get.side_effect = [
        httpx.Response(200, json=mock_player_clan_response, headers=JSON_CONTENT_TYPE),
        httpx.Response(404, json={"errors": [{"title": "Not Found"}]}, headers=JSON_CONTENT_TYPE)
    ]
    
    with pytest.raises(ClanNotFoundAPIError) as excinfo:
        await pubg_api.get_player_clan_details(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    assert f"clan with id '{SAMPLE_CLAN_ID.lower()}' not found" in str(excinfo.value).lower() # by_player=False message


# --- Cache Tests ---
@pytest.mark.asyncio
async def test_get_player_id_caching(mock_httpx_client):
    mock_response_data = {"data": [{"id": SAMPLE_ACCOUNT_ID, "type": "player"}]}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)

    # Call 1 - should hit API
    await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    mock_httpx_client.get.assert_called_once() 
    
    # Call 2 - should use cache
    await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    mock_httpx_client.get.assert_called_once() # Still called once due to cache

    # Call 3 with different params - should hit API again
    await pubg_api.get_player_id("another_player", SAMPLE_PLATFORM)
    assert mock_httpx_client.get.call_count == 2

@pytest.mark.asyncio
async def test_get_match_history_ids_cache_short_ttl(mock_httpx_client):
    # This test is conceptual for short TTL. Pytest doesn't easily manipulate time for aiocache's default timer.
    # We rely on the TTL being set correctly (120s) and assume aiocache handles it.
    # We'll test that it caches at least once.
    mock_response_data = {"data": {"relationships": {"matches": {"data": [{"id": "m1"}]}}}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=mock_response_data, headers=JSON_CONTENT_TYPE)

    await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    mock_httpx_client.get.assert_called_once()

    await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    mock_httpx_client.get.assert_called_once() # Should be cached for its short TTL

    # To truly test TTL expiry, one would need to:
    # 1. Use a time-controllable cache backend (like aiocache.testing.FakeRedis)
    # 2. Or, use `asyncio.sleep` to wait past TTL (makes tests slow)
    # 3. Or, manually manipulate cache entry expiry if backend allows (not typical for SimpleMemoryCache)
    # For this test, we assume the TTL mechanism of aiocache works as specified by its docs.
    # Example using asyncio.sleep (would make test take > 2 mins, so commented out):
    # print("Waiting for match history cache to expire (120s)...")
    # await asyncio.sleep(121)
    # await pubg_api.get_player_match_history_ids(SAMPLE_ACCOUNT_ID, SAMPLE_PLATFORM)
    # assert mock_httpx_client.get.call_count == 2
    pass

@pytest.mark.asyncio
async def test_cache_key_uniqueness(mock_httpx_client):
    # Test that different functions or different args produce different cache entries
    # and don't incorrectly hit cache from another function/call.
    
    # Mock for get_player_id
    player_data = {"data": [{"id": SAMPLE_ACCOUNT_ID, "type": "player"}]}
    mock_httpx_client.get.return_value = httpx.Response(200, json=player_data, headers=JSON_CONTENT_TYPE)
    await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    assert mock_httpx_client.get.call_count == 1
    
    # Mock for get_match_details (different endpoint, different args)
    match_data = {"data": {"type": "match", "id": SAMPLE_MATCH_ID}}
    mock_httpx_client.get.return_value = httpx.Response(200, json=match_data, headers=JSON_CONTENT_TYPE)
    await pubg_api.get_match_details(SAMPLE_MATCH_ID, SAMPLE_PLATFORM)
    assert mock_httpx_client.get.call_count == 2 # Incremented, so it didn't use get_player_id's cache

    # Call get_player_id again, should be cached
    await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    assert mock_httpx_client.get.call_count == 2 # Still 2, used cache for get_player_id

    # Call get_match_details again, should be cached
    await pubg_api.get_match_details(SAMPLE_MATCH_ID, SAMPLE_PLATFORM)
    assert mock_httpx_client.get.call_count == 2 # Still 2, used cache for get_match_details

@pytest.mark.asyncio
async def test_api_key_not_configured():
    # Temporarily patch the module-level PUBG_API_KEY variable to None for this test
    # This simulates the scenario where os.getenv("PUBG_API_KEY") returned None at module load.
    with patch('app.pubg_api.PUBG_API_KEY', None):
        with pytest.raises(UnauthorizedErrorAPI) as excinfo:
            await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
        assert "PUBG API Key is not configured" in str(excinfo.value) # Check for the specific message

@pytest.mark.asyncio
async def test_module_import_and_logging_with_missing_api_key(monkeypatch, caplog, mock_httpx_client):
    """
    Tests that the module imports successfully even if PUBG_API_KEY is not set,
    that a critical log message is emitted, and that API calls fail correctly.
    """
    # 1. Ensure the environment variable is not set
    monkeypatch.delenv("PUBG_API_KEY", raising=False)

    # 2. Reload the pubg_api module to trigger its module-level code again
    import importlib
    importlib.reload(pubg_api) # This re-runs the os.getenv("PUBG_API_KEY") and the check

    # 3. Check that the module-level PUBG_API_KEY is now None
    assert pubg_api.PUBG_API_KEY is None, "Module-level PUBG_API_KEY should be None after reload with unset env var"

    # 4. Check for the critical log message
    assert "CRITICAL: PUBG_API_KEY environment variable not set or empty. API calls will fail if attempted." in caplog.text
    # Ensure it's logged at CRITICAL level
    assert any(record.levelno == logging.CRITICAL for record in caplog.records)

    # 5. Verify that an attempt to make an API call now fails with UnauthorizedErrorAPI
    # The mock_httpx_client is needed because _make_request will be called up to the point of get_headers()
    with pytest.raises(UnauthorizedErrorAPI, match="PUBG API Key is not configured"):
        await pubg_api.get_player_id(SAMPLE_PLAYER_NAME, SAMPLE_PLATFORM)
    
    # 6. Restore the API_KEY for other tests if necessary (though pytest isolation should handle this)
    # For safety, if other tests might rely on a globally patched os.environ, reset it.
    # However, monkeypatch usually handles cleanup.
    # If API_KEY was set in the test environment for other tests, it might need to be restored.
    # This depends on how the overall test session environment is configured.
    # For now, assume monkeypatch cleans up its own changes to os.environ.
    # To be absolutely sure for subsequent tests in the same session (if any were to run in a way that
    # bypasses pytest's usual isolation or if pubg_api is not reloaded again), we could reset it:
    original_key = "dummy_key_for_testing_restore" # A placeholder, actual key isn't used by mocks
    monkeypatch.setenv("PUBG_API_KEY", original_key)
    importlib.reload(pubg_api)
    assert pubg_api.PUBG_API_KEY == original_key


# Add more tests for other functions (get_player_seasonal_stats, get_player_weapon_summaries, etc.)
# following the same patterns: success, various errors, caching.
# For brevity in this example, I've covered the main patterns.

# Summary of `tests/test_pubg_api.py` after changes:
# *   `test_api_key_not_configured`: Now correctly patches `app.pubg_api.PUBG_API_KEY` (the actual module-level variable)
#     to `None` and asserts that `UnauthorizedErrorAPI` is raised with the specific message from `get_headers()`.
# *   `test_module_import_and_logging_with_missing_api_key`: New test added.
#     *   Uses `monkeypatch.delenv` to remove `PUBG_API_KEY` from environment.
#     *   Uses `importlib.reload(pubg_api)` to force re-evaluation of the module-level code in `pubg_api`.
#     *   Asserts that `pubg_api.PUBG_API_KEY` becomes `None` after this reload.
#     *   Uses `caplog` fixture to capture log messages and asserts that the critical warning about the missing API key is logged.
#     *   Finally, asserts that an attempt to call an API function (`get_player_id`) raises `UnauthorizedErrorAPI`.
#     *   Includes a step to restore `PUBG_API_KEY` in the environment using `monkeypatch.setenv` and reloads `pubg_api` again
#       to ensure a clean state for subsequent tests, preventing side effects.
# *   Other tests remain largely the same, as they test API call logic assuming a key *is* configured (or the mock bypasses the key check part).
# *   The overall test suite now more accurately reflects the deferred failure mechanism for the API key.
