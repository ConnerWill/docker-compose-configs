from django.core.cache import cache


def clear_caches():
    for k in ["vendors_footer", "should_render_extra_vendors"]:
        cache.delete(k)
