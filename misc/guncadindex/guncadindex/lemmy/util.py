import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Lemmy stuff
REQUEST_TYPES = ["All", "Communities", "Posts", "Comments", "Users", "Url"]
LOCALITIES = ["All", "Local"]
SORTS = [
    "Active",
    "Hot",
    "New",
    "Old",
    "TopDay",
    "TopWeek",
    "TopMonth",
    "TopYear",
    "TopAll",
    "MostComments",
    "NewComments",
    "TopHour",
    "TopSixHour",
    "TopTwelveHour",
    "TopThreeMonths",
    "TopSixMonths",
    "TopNineMonths",
    "Controversial",
    "Scaled",
]

# Internal configuration
INSTANCE_WHITELIST = settings.GUNCAD_LEMMY_INSTANCE_WHITELIST
HEADERS = {
    "User-Agent": f"GunCADIndex-LemmyAgent/1.0 (https://guncadindex.com) {requests.utils.default_user_agent()}"
}
INSTANCE = f"{settings.GUNCAD_LEMMY_INSTANCE}{settings.GUNCAD_LEMMY_INSTANCE_ENDPOINT if not settings.GUNCAD_LEMMY_INSTANCE_ENDPOINT == "None" else ''}"
STATS_INSTANCE = f"{settings.GUNCAD_LEMMY_STATS_URL}"


_requests_retries = Retry(
    total=10,
    backoff_factor=2,
    status_forcelist=[400, 429, 500, 502, 503, 504],
    respect_retry_after_header=True,
)
_adapter = HTTPAdapter(max_retries=_requests_retries)
_session = requests.Session()
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


def search(
    query,
    request_type="All",
    sort="TopAll",
    locality="All",
    pagelimit=10,
    itemlimit=10,
):
    """
    Search the configured Lemmy instance for objects matching some query
        query           str     The search query to send. If a list, will iterate over all queries and return all their results concatenated
        request_type    str     The type of activity you're looking for. See REQUEST_TYPES
        sort            str     How to sort the results. See SORTS
        locality        str     Should we include remote results? See LOCALITIES
        pagelimit       int     How many pages deep we should traverse for this search. Each page will have:
        itemlimit       int     How many items we should ask for with each request
    """
    assert request_type in REQUEST_TYPES
    assert locality in LOCALITIES
    assert sort in SORTS
    response_dicts = [
        ("comments", "comment"),
        ("posts", "post"),
        ("communities", "community"),
        ("users", "user"),
    ]
    all_items = {key[0]: {} for key in response_dicts}
    url = f"{INSTANCE}/search"
    queries = query if type(query) == list else [query]
    for query in queries:
        if not query:
            continue
        page = 1
        while True:
            r = _session.get(
                url,
                params={
                    "q": query,
                    "type_": request_type,
                    "listing_type": locality,
                    "page": page,
                    "limit": itemlimit,
                },
                headers=HEADERS,
            )
            r.raise_for_status()
            data = r.json()
            shouldbreak = True
            for key, obj in response_dicts:
                items = data.get(key, [])
                if not items:
                    continue
                shouldbreak = False
                for item in items:
                    ap_id = item.get(obj, {}).get("ap_id", "")
                    if not ap_id or (
                        INSTANCE_WHITELIST
                        and not any(inst in ap_id for inst in INSTANCE_WHITELIST)
                    ):
                        continue
                    all_items[key][ap_id] = item
            page += 1
            if shouldbreak or page > pagelimit:
                break
    # We eliminate the ap_id keys and flatten out to a list because it works
    # out more nicely for DB stuff later, like querying post counts
    return {k: list(v.values()) for k, v in all_items.items()}
