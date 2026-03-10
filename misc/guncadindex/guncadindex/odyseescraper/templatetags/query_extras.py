from urllib.parse import urlencode

from django import template

register = template.Library()


@register.filter
def remove_query_param(querydict, key):
    """
    Remove *all* occurrences of `key` from a QueryDict (or dict-like),
    and return a URL-encoded string of the remaining params.
    """
    params = querydict.copy()
    params.pop(key, None)
    return params.urlencode()


@register.simple_tag
def url_replace(request, **kwargs):
    """
    Copy request.GET, then for each kwarg:
      - if value is None: remove that key
      - else: set the key to that value (overwriting any existing)
    Returns a urlencoded string.
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params.setlist(key, value if isinstance(value, list) else [value])
    return params.urlencode()


@register.filter
def without(value_list, drop):
    """
    Return a new list that omits `drop`.
    """
    return [v for v in value_list if v != drop]
