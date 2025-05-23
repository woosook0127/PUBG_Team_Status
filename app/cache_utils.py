from aiocache import Cache, caches
from aiocache.serializers import JsonSerializer

# Configure a simple in-memory cache as default
# For production, consider 'aiocache.MemcachedCache' or 'aiocache.RedisCache'
# if you have memcached or redis available.
# Default TTL can be set here, or per @cached decorator.
caches.set_config({
    'default': {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.JsonSerializer"
        }
    },
    # Example for a longer TTL cache if needed for specific items
    'long_ttl': {
        'cache': "aiocache.SimpleMemoryCache",
        'ttl': 3600 * 24, # 24 hours
        'serializer': {
            'class': "aiocache.serializers.JsonSerializer"
        }
    }
})

# You can export specific cache instances if you want to use different configurations easily
default_cache = caches.get('default')
long_ttl_cache = caches.get('long_ttl')

# Or just use the @cached decorator with cache='default' or cache='long_ttl'
# Example of how to use the decorator in other files:
# from .cache_utils import default_cache
# from aiocache import cached
#
# @cached(ttl=60, cache=default_cache, key_builder=lambda f, *args, **kwargs: f"{f.__name__}_{args}_{kwargs}")
# async def my_function(param1, param2):
# pass
#
# The key_builder is important to make keys unique based on function name and arguments.
# A default key_builder is provided by aiocache if you don't specify one,
# but it's good practice to be explicit for clarity and control.

def default_key_builder(func, *args, **kwargs):
    # Creates a cache key based on function module, name, args, and sorted kwargs
    # Similar to aiocache's default key builder but ensures kwargs order doesn't break cache.
    ordered_kwargs = tuple(sorted(kwargs.items()))
    return f"{func.__module__}.{func.__name__}:{args!r}:{ordered_kwargs!r}"
