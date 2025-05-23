class APIError(Exception):
    """Base class for API related errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

class PlayerNotFoundAPIError(APIError):
    def __init__(self, player_identifier: str, platform: str):
        super().__init__(f"Player '{player_identifier}' not found on platform '{platform}'.", 404)

class SeasonNotFoundAPIError(APIError):
    def __init__(self, account_id: str, season_id: str, platform: str):
        super().__init__(f"Season data for season '{season_id}' not found for player '{account_id}' on platform '{platform}'.", 404)

class ClanNotFoundAPIError(APIError):
    def __init__(self, identifier: str, platform: str, by_player: bool = True):
        message = f"Clan not found for player '{identifier}' on platform '{platform}'." if by_player \
                  else f"Clan with ID '{identifier}' not found on platform '{platform}'."
        super().__init__(message, 404)

class MatchNotFoundAPIError(APIError):
    def __init__(self, match_id: str, platform: str):
        super().__init__(f"Match with ID '{match_id}' not found on platform '{platform}'.", 404)

class RateLimitErrorAPI(APIError):
    def __init__(self, message="External API rate limit potentially exceeded or too many concurrent requests."):
        super().__init__(message, 429)

class UnauthorizedErrorAPI(APIError):
    def __init__(self, message="Unauthorized access to external API. Check API Key."):
        super().__init__(message, 401)

class ForbiddenErrorAPI(APIError):
    def __init__(self, message="Access to external API resource is forbidden."):
        super().__init__(message, 403)

class ExternalAPIServiceError(APIError):
    def __init__(self, message="External API service unavailable or returned an error.", status_code=503):
        super().__init__(message, status_code)

class BadRequestAPIError(APIError):
    def __init__(self, message="Bad request to external API."):
        super().__init__(message, 400)
