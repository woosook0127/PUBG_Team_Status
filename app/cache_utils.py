from aiocache import caches, Cache
from aiocache.backends.memory import SimpleMemoryCache # Import the actual class
from aiocache.serializers import JsonSerializer # Import the actual class

# Configure caches using direct class references and serializer instances
caches.set_config({
    'default': {
        'cache': SimpleMemoryCache, # Pass the class directly
        'serializer': JsonSerializer(), # Pass an instance of the serializer
        'namespace': "main" # Add a namespace for easier clearing if needed
    },
    'long_ttl': {
        'cache': SimpleMemoryCache, # Pass the class directly
        'ttl': 3600 * 24, # 24 hours
        'serializer': JsonSerializer(), # Pass an instance
        'namespace': "long"
    }
})

# Make specific cache instances available if needed, or just rely on aliases.
# These calls also ensure the configuration is processed.
default_cache_instance = caches.get('default')
long_ttl_cache_instance = caches.get('long_ttl')

# Custom key builder (remains the same)
def default_key_builder(func, *args, **kwargs):
    ordered_kwargs = tuple(sorted(kwargs.items()))
    return f"{func.__module__}.{func.__name__}:{args!r}:{ordered_kwargs!r}"

# Ensure cache_utils is imported early in app/main.py or before pubg_api.py
# by other modules if this configuration needs to be globally available before
# any @cached decorator is processed.
# For now, app/pubg_api.py imports default_key_builder from here,
# so this file will be processed when pubg_api.py is imported.
# The critical part is that SimpleMemoryCache and JsonSerializer are resolved
# class objects when set_config is called.
