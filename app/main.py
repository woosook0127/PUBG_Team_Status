from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from . import pubg_api
from . import team_analyzer
from .weapon_utils import get_weapon_category, get_platform_shard
from .exceptions import ( # Import custom exceptions
    APIError, PlayerNotFoundAPIError, SeasonNotFoundAPIError, ClanNotFoundAPIError,
    MatchNotFoundAPIError, RateLimitErrorAPI, UnauthorizedErrorAPI, ForbiddenErrorAPI,
    ExternalAPIServiceError, BadRequestAPIError
)


# Pydantic Models for Individual Weapon Stats
class WeaponStat(BaseModel): # Retaining existing models for clarity
    weapon_id: str
    category: str
    total_damage: float
    kills: int
    dpm: float
    matches_played_with_weapon: Optional[int] = None

class IndividualWeaponStatsResponse(BaseModel): # Retaining existing models
    player_name: str
    platform: str
    season_id: str
    total_matches_played: int
    top_weapons_by_category: Dict[str, WeaponStat]

# Pydantic Models for Team Identification (existing)
class IdentifiedTeamResponse(BaseModel):
    player_name: str
    platform: str
    team_member_account_ids: Optional[List[str]] = None
    identification_method: str
    # Match details are not part of this specific response model, handled internally

# Pydantic Models for Team Performance Comparison
class TeammatePerformanceStat(BaseModel):
    teammate_account_id: str
    teammate_name: Optional[str] = None # Future: resolve names
    matches_played_together: int
    avg_kills: float
    avg_damage_dealt: float
    avg_survival_time_seconds: float
    avg_match_rank: float # Lower is better
    avg_assists: float

class TeamPerformanceComparisonResponse(BaseModel):
    player_name: str
    platform: str
    season_id: str # The season for which performance was requested
    identified_team_method: str # From team_analyzer
    team_performance_stats: List[TeammatePerformanceStat]

# Pydantic Models for Overall Team Stats
class OverallTeamStatsData(BaseModel):
    avg_team_kills: float
    avg_team_damage: float
    avg_team_survival_time: float
    avg_team_match_rank: float
    matches_played_as_full_team: int
    message: str # Message about the stats calculation (e.g., number of matches, or why no stats)

class OverallTeamStatsResponse(BaseModel):
    player_name: str
    platform: str
    season_id: str
    # identified_team_ids: Optional[List[str]] = None # Not strictly needed if stats have a message
    overall_stats: OverallTeamStatsData


app = FastAPI(
    title="PUBG Stats API Wrapper",
    description="A FastAPI service for PUBG stats, including team identification, individual performance, and overall team stats, with enhanced error handling and caching.",
    version="0.6.0", # Version updated
)

# Mount the static directory to serve frontend files
app.mount("/ui", StaticFiles(directory="static", html=True), name="static-ui")

# Global Exception Handlers
@app.exception_handler(APIError)
async def custom_api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}, # Using "detail" to match FastAPI's HTTPException
    )

@app.exception_handler(PlayerNotFoundAPIError)
async def player_not_found_error_handler(request: Request, exc: PlayerNotFoundAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(SeasonNotFoundAPIError)
async def season_not_found_error_handler(request: Request, exc: SeasonNotFoundAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(ClanNotFoundAPIError)
async def clan_not_found_error_handler(request: Request, exc: ClanNotFoundAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(MatchNotFoundAPIError)
async def match_not_found_error_handler(request: Request, exc: MatchNotFoundAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(RateLimitErrorAPI)
async def rate_limit_error_handler(request: Request, exc: RateLimitErrorAPI):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(UnauthorizedErrorAPI)
async def unauthorized_error_handler(request: Request, exc: UnauthorizedErrorAPI):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(ForbiddenErrorAPI)
async def forbidden_error_handler(request: Request, exc: ForbiddenErrorAPI):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
    
@app.exception_handler(ExternalAPIServiceError)
async def external_api_service_error_handler(request: Request, exc: ExternalAPIServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.exception_handler(BadRequestAPIError)
async def bad_request_api_error_handler(request: Request, exc: BadRequestAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

# Catch-all for other HTTPException (e.g., from FastAPI's own validation)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# VALID_PLATFORMS now derived from weapon_utils.PLATFORM_SHARD_MAP keys
VALID_PLATFORMS_DISPLAY = set(key.lower() for key in get_platform_shard.__globals__['PLATFORM_SHARD_MAP'].keys())


@app.get("/") # Root path now can serve a general message or redirect to UI
async def read_root():
    return {"message": "Welcome to the PUBG Stats API Wrapper. Access the UI at /ui/index.html. See /docs for API endpoint details."}


@app.get("/players/{platform_display_name}/{player_name}/identified-team", response_model=IdentifiedTeamResponse)
async def get_identified_player_team(
    platform_display_name: str,
    player_name: str
):
    platform_shard = get_platform_shard(platform_display_name)
    if not platform_shard:
        # This will be caught by the generic HTTPException handler if not overridden
        # Or we can define a specific exception for invalid input parameters
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform_display_name}'. Valid are: {', '.join(VALID_PLATFORMS_DISPLAY)}")

    # 1. Get Player ID from Player Name
    # Errors from pubg_api (like PlayerNotFoundAPIError) will be caught by global handlers
    player_data_response = await pubg_api.get_player_id(player_name, platform_shard)
    
    # The new pubg_api functions raise exceptions instead of returning dicts with "error" keys.
    # So, we directly access data assuming success if no exception was raised.
    if not player_data_response.get("data"): # Should not happen if API contract is followed (empty list for no players)
        # This case might indicate an unexpected API response not covered by specific exceptions
        raise APIError(f"Player data for '{player_name}' on platform '{platform_display_name}' was empty or malformed.", status_code=500)
        
    main_player_account_id = player_data_response["data"][0]["id"]

    # 2. Call the team identification logic
    team_member_ids, identification_method, _ = await team_analyzer.identify_player_team( # _ for processed_matches
        main_player_account_id, platform_shard, pubg_api
    )
    
    return IdentifiedTeamResponse(
        player_name=player_name, 
        platform=platform_display_name,
        team_member_account_ids=team_member_ids,
        identification_method=identification_method
    )

@app.get("/players/{platform_display_name}/{player_name}/seasons/{season_id}/team-performance-comparison", response_model=TeamPerformanceComparisonResponse)
async def get_team_performance_comparison(
    platform_display_name: str,
    player_name: str,
    season_id: str 
):
    platform_shard = get_platform_shard(platform_display_name)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform_display_name}'.")

    # 1. Get Player ID
    player_data_resp = await pubg_api.get_player_id(player_name, platform_shard)
    # Assuming player_data_resp["data"][0]["id"] exists if no exception.
    main_player_account_id = player_data_resp["data"][0]["id"]

    # 2. Identify team and get processed match details from team_analyzer
    # This reuses the match data fetched during team identification.
    # team_analyzer.identify_player_team now returns:
    identified_team_ids, id_method, processed_match_details = await team_analyzer.identify_player_team(
        main_player_account_id, platform_shard, pubg_api
    )

    if not identified_team_ids:
        return TeamPerformanceComparisonResponse(
            player_name=player_name,
            platform=platform_display_name,
            season_id=season_id,
            identified_team_method=id_method, 
            team_performance_stats=[]
        )
        
    from . import team_performance 
    
    performance_stats_dicts = team_performance.calculate_team_performance_from_matches(
        main_player_account_id=main_player_account_id,
        team_member_account_ids=identified_team_ids,
        processed_match_details_list=processed_match_details,
        requested_season_id=season_id 
    )
    
    teammate_stats_models = [TeammatePerformanceStat(**stat) for stat in performance_stats_dicts]

    return TeamPerformanceComparisonResponse(
        player_name=player_name,
        platform=platform_display_name,
        season_id=season_id,
        identified_team_method=id_method,
        team_performance_stats=teammate_stats_models
    )

@app.get("/players/{platform_display_name}/{player_name}/seasons/{season_id}/overall-team-stats", response_model=OverallTeamStatsResponse)
async def get_overall_team_stats_endpoint(
    platform_display_name: str,
    player_name: str,
    season_id: str
):
    platform_shard = get_platform_shard(platform_display_name)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform_display_name}'.")

    # 1. Get Player ID
    player_data_resp = await pubg_api.get_player_id(player_name, platform_shard)
    main_player_account_id = player_data_resp["data"][0]["id"]

    # 2. Identify team and get processed match details from team_analyzer
    identified_team_ids, _, processed_match_details = await team_analyzer.identify_player_team(
        main_player_account_id, platform_shard, pubg_api
    )

    # 3. Calculate overall team stats
    from . import team_performance 

    if not identified_team_ids or len(identified_team_ids) < 2:
        stats_data = {
            "avg_team_kills": 0.0, "avg_team_damage": 0.0,
            "avg_team_survival_time": 0.0, "avg_team_match_rank": 0.0,
            "matches_played_as_full_team": 0,
            "message": "No valid team identified (requires at least 2 members) to calculate overall stats."
        }
    else:
        stats_data = team_performance.calculate_overall_team_stats(
            team_member_account_ids=identified_team_ids,
            processed_match_details_list=processed_match_details,
            requested_season_id=season_id 
        )
    
    overall_stats_model = OverallTeamStatsData(**stats_data)

    return OverallTeamStatsResponse(
        player_name=player_name,
        platform=platform_display_name,
        season_id=season_id,
        overall_stats=overall_stats_model
    )


@app.get("/players/{platform_display_name}/{player_name}/seasons/{season_id}/individual-weapon-stats", response_model=IndividualWeaponStatsResponse)
async def get_individual_weapon_stats(
    platform_display_name: str,
    player_name: str,
    season_id: str
):
    platform_shard = get_platform_shard(platform_display_name)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform_display_name}'.")

    # 1. Get Player ID
    player_data = await pubg_api.get_player_id(player_name, platform_shard)
    account_id = player_data["data"][0]["id"]

    # 2. Get Player Weapon Summaries
    weapon_summaries_data = await pubg_api.get_player_weapon_summaries(account_id, season_id, platform_shard)
    
    # 3. Get Player Seasonal Stats
    seasonal_stats_data = await pubg_api.get_player_seasonal_stats(account_id, season_id, platform_shard)

    total_matches_played = 0
    game_mode_stats = seasonal_stats_data.get("data", {}).get("attributes", {}).get("gameModeStats", {})
    for mode_stats in game_mode_stats.values():
        total_matches_played += mode_stats.get("roundsPlayed", 0)
    
    if total_matches_played == 0:
        pass # DPM will be calculated as 0.0

    top_weapons_by_category: Dict[str, WeaponStat] = {}
    weapon_stats_list = weapon_summaries_data.get("data", {}).get("attributes", {}).get("weaponSummaries", {})

    for weapon_id, stats in weapon_stats_list.items():
        category = get_weapon_category(weapon_id)
        if category == "Other" or category == "Pistol" or category == "Melee": 
            continue

        current_damage = stats.get("damageDealt", 0.0)
        current_kills = stats.get("kills", 0)
        dpm = (current_damage / total_matches_played) if total_matches_played > 0 else 0.0

        if category not in top_weapons_by_category or current_damage > top_weapons_by_category[category].total_damage:
            top_weapons_by_category[category] = WeaponStat(
                weapon_id=weapon_id, category=category, total_damage=current_damage,
                kills=current_kills, dpm=dpm
            )
            
    return IndividualWeaponStatsResponse(
        player_name=player_name, platform=platform_display_name, season_id=season_id,
        total_matches_played=total_matches_played, top_weapons_by_category=top_weapons_by_category
    )

# Simplified existing endpoints to use the new error handling implicitly
@app.get("/player/{platform}/{player_name}/id") # platform is display name
async def get_player_id_endpoint(platform: str, player_name: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    # PlayerNotFoundAPIError will be handled globally if raised by pubg_api
    return await pubg_api.get_player_id(player_name, platform_shard)

@app.get("/player/{platform}/{account_id}/season/{season_id}/stats") # platform is display name
async def get_player_seasonal_stats_endpoint(platform: str, account_id: str, season_id: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    # SeasonNotFoundAPIError etc. will be handled globally
    return await pubg_api.get_player_seasonal_stats(account_id, season_id, platform_shard)

@app.get("/player/{platform}/{account_id}/season/{season_id}/weapons") # platform is display name
async def get_player_weapon_summaries_endpoint(platform: str, account_id: str, season_id: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    return await pubg_api.get_player_weapon_summaries(account_id, season_id, platform_shard)

@app.get("/player/{platform}/{account_id}/matches") # platform is display name
async def get_player_match_history_ids_endpoint(platform: str, account_id: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    match_ids = await pubg_api.get_player_match_history_ids(account_id, platform_shard)
    # The API returns a list of strings directly now, or raises an exception.
    # Previous check for dict and "error" key is no longer needed.
    if not match_ids: # Empty list, but not an error dict
        return {"message": "No match history found or player does not exist.", "data": []}
    return {"match_ids": match_ids}

@app.get("/match/{platform}/{match_id}/details") # platform is display name
async def get_match_details_endpoint(platform: str, match_id: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    return await pubg_api.get_match_details(match_id, platform_shard)

@app.get("/player/{platform}/{account_id}/clan") # platform is display name
async def get_player_clan_details_endpoint(platform: str, account_id: str):
    platform_shard = get_platform_shard(platform)
    if not platform_shard:
        raise HTTPException(status_code=400, detail=f"Invalid platform display name '{platform}'.")
    # ClanNotFoundAPIError etc. will be handled globally
    return await pubg_api.get_player_clan_details(account_id, platform_shard)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
