from aiolimiter import AsyncLimiter

# Rate limit: 10 requests per minute (60 seconds)
RATE_LIMIT = 10
PERIOD = 60
limiter = AsyncLimiter(RATE_LIMIT, PERIOD)
