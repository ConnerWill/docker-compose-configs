import hashlib

from django.core import signing
from django.core.cache import cache

URL_KEY_LENGTH = 8  # How many characters to use for URL keys
URL_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days


def get_key_for_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:URL_KEY_LENGTH]


def store_outbound_url(url: str) -> str:
    key = get_key_for_url(url)
    cache.set(f"out:{key}", url, URL_CACHE_TTL)
    return key


def retrieve_outbound_url(key: str):
    url = cache.get(f"out:{key}", None)
    return url
