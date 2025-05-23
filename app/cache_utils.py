from aiocache import caches, Cache
from aiocache.backends.memory import SimpleMemoryCache # Import the actual class
from aiocache.serializers import JsonSerializer # Import the actual class

# Configure caches using direct class references for 'cache'
# and a dict with 'class': SerializerClass for 'serializer'.
caches.set_config({
    'default': {
        'cache': SimpleMemoryCache,           # Correct: Pass the class directly
        'serializer': {'class': JsonSerializer}, # Correct: Pass a dict with the class
        'namespace': "main"                   # Add a namespace for easier clearing
    },
    'long_ttl': {
        'cache': SimpleMemoryCache,           # Correct: Pass the class directly
        'serializer': {'class': JsonSerializer}, # Correct: Pass a dict with the class
        'ttl': 3600 * 24,                     # 24 hours (example specific TTL for this alias)
        'namespace': "long_ttl_ns"            # Use a different namespace for clarity
    }
})

# These calls will now work correctly as the config format is valid.
# They also ensure the configuration is processed upon module import.
default_cache_instance = caches.get('default')
long_ttl_cache_instance = caches.get('long_ttl') # Corrected namespace for this example

# Custom key builder (remains the same)
def default_key_builder(func, *args, **kwargs):
    ordered_kwargs = tuple(sorted(kwargs.items()))
    return f"{func.__module__}.{func.__name__}:{args!r}:{ordered_kwargs!r}"

# app/pubg_api.py imports default_key_builder from here,
# so this file (and caches.set_config) will be processed when pubg_api.py is imported.
# This ensures the cache is configured before @cached decorators are applied.
