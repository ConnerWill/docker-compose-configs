import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

lbrynet_api_url = settings.GUNCAD_LBRYNET_URL
user_agent = (
    f"GunCADIndex (https://guncadindex.com) {requests.utils.default_user_agent()}"
)

common_claim_search_bad_value_types = [
    "repost",  # We should get this one from the OG source
    "collection",  # Playlists are irrelevant to our needs
]
common_claim_search_bad_stream_types = [
    "video"  # Somehow, even with filtering, we get videos
]
common_claim_search_args = {
    "stream_types": ["binary", "model"],
    "remove_duplicates": True,
    "fee_amount": "<=0",
    "has_source": True,
    "not_tags": ["c:purchase", "c:members-only", "noindex", "nobot", "nobots"],
}


def wait_for_component(component, poll_wait=1):
    """
    Waits for a LBRY component to have initialized

        component   The component to wait for
        poll_wait   How long to wait in-between each polling

    Returns False if we can't find that component, otherwise True whwen it
    finishes initializing
    """
    # Boilerplate setup, gearing up for retries n stuff
    sleepduration = 1
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    payload = {"method": "status"}
    while True:
        response = session.post(lbrynet_api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {}).get("startup_status", {})
        if result.get(component, False):
            return True
        elif not component in result.keys():
            return False
        time.sleep(poll_wait)


def resolve(handle):
    """
    Calls the resolve method in LBRY, attempting to resolve the handle supplied to a claim ID
    """
    payload = {
        "method": "resolve",
        "params": {
            "urls": handle,
        },
    }
    response = requests.post(lbrynet_api_url, json=payload)
    response.raise_for_status()
    obj = response.json()["result"][handle]
    if obj.get("error", False):
        return {}
    return obj


def get_one_degree(ids, maxqueries=5000):
    """
    Gets all channels that are one degree of separation away from the given list of channels
    by analyzing reposts.
    """
    assert type(ids) == list
    oldestclaim = time.time()
    claims = []
    for i in range(1, maxqueries):
        stale_oldestclaim = oldestclaim
        first_payload = {
            "method": "claim_search",
            "params": {
                "channel_ids": ids,
                "order_by": "timestamp",
                "timestamp": f"<{oldestclaim}",
                "page_size": 100,
                "stream_types": ["repost"],
                "remove_duplicates": True,
                "fee_amount": "<=0",
                "has_source": True,
                "not_tags": ["c:members-only"],
            }
            | common_claim_search_args,
        }
        # Note: not a magic number here. The LBRY API supports 1000 claims in a single query.
        # Thus, the 100 claims per page and the 10 iterations we do here matches as much as we
        # can without reformulating the query
        # Parallelize page requests
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    requests.post,
                    lbrynet_api_url,
                    json={
                        **first_payload,
                        "params": {**first_payload["params"], "page": i},
                    },
                ): i
                for i in range(1, 11)
            }

            for future in as_completed(futures):
                response = future.result()
                response.raise_for_status()
                data = response.json()
                items = data.get("result", {}).get("items", [])
                for item in items:
                    channel = item.get("reposted_claim", {}).get("signing_channel", {})
                    if (
                        channel
                        and channel.get("claim_id", False)
                        and channel.get("claim_id") not in ids
                        and not channel.get("claim_id") in claims
                    ):
                        claimid = channel.get("claim_id")
                        claims.append(claimid)
                        yield (claimid, channel)
                    if item.get("timestamp") < oldestclaim:
                        oldestclaim = item.get("timestamp")

        if stale_oldestclaim == oldestclaim:
            break
    return


def bulk_claim_search(ids, extra_args={}, maxqueries=5000):
    """
    Calls the claim_search method in LBRY, attempting to find everything for a bunch of channels
    Returns nested dicts:
    {
    channelid: {
        releaseid: {},
        [...]
        },
    [...]
    Also note that maxpages behaves differently here. The maximum
    }
    """
    assert type(ids) == list
    oldestclaim = time.time()
    claims = {claimid: {} for claimid in ids}
    for i in range(1, maxqueries):
        stale_oldestclaim = oldestclaim
        first_payload = {
            "method": "claim_search",
            "params": {
                "channel_ids": ids,
                "order_by": "timestamp",
                "timestamp": f"<{oldestclaim}",
                "page_size": 100,
            }
            | common_claim_search_args
            | extra_args,
        }
        # Note: not a magic number here. The LBRY API supports 1000 claims in a single query.
        # Thus, the 100 claims per page and the 10 iterations we do here matches as much as we
        # can without reformulating the query
        # Parallelize page requests
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    requests.post,
                    lbrynet_api_url,
                    json={
                        **first_payload,
                        "params": {**first_payload["params"], "page": i},
                    },
                ): i
                for i in range(1, 11)
            }

            for future in as_completed(futures):
                response = future.result()
                response.raise_for_status()
                data = response.json()
                items = data.get("result", {}).get("items", [])
                for item in items:
                    try:
                        if (
                            item.get("value_type", "")
                            in common_claim_search_bad_value_types
                            or item.get("value", {}).get("stream_type", "")
                            in common_claim_search_bad_stream_types
                        ):
                            continue
                        claims[item["signing_channel"]["claim_id"]][
                            item["claim_id"]
                        ] = item
                        if item.get("timestamp") < oldestclaim:
                            oldestclaim = item.get("timestamp")
                    except Exception as e:
                        logger.warning(f"Error while doing a bulk claim search: {e}")
                        logger.exception(e)
                        logger.warning(f"Problematic item: {item or None}")

        if stale_oldestclaim == oldestclaim:
            break
    return claims


def channel_search_by_streams_with_tag(tags, not_channel_ids=[], maxqueries=5000):
    """
    Calls the claim_search method in LBRY, attempting to find all channel claims given a list
    of tags. Defaults to some standard GunCAD creator tags.
    Populate not_channel_ids with a list of existing claim IDs for increased efficiency
    """
    assert type(tags) == list
    assert type(not_channel_ids) == list
    oldestclaim = time.time()
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    for i in range(1, maxqueries):
        stale_oldestclaim = oldestclaim
        first_payload = {
            "method": "claim_search",
            "params": {
                "remove_duplicates": True,
                "any_tags": tags,
                "order_by": "timestamp",
                "timestamp": f"<{oldestclaim}",
                "claim_type": "stream",
                "page_size": 100,
                "not_channel_ids": not_channel_ids,
            }
            | common_claim_search_args,
        }
        first_payload["params"]["not_tags"] += ["c:unlisted"]
        # Note: not a magic number here. The LBRY API supports 1000 claims in a single query.
        # Thus, the 100 claims per page and the 10 iterations we do here matches as much as we
        # can without reformulating the query
        # Parallelize page requests
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    session.post,
                    lbrynet_api_url,
                    json={
                        **first_payload,
                        "params": {**first_payload["params"], "page": i},
                    },
                ): i
                for i in range(1, 11)
            }

            for future in as_completed(futures):
                response = future.result()
                response.raise_for_status()
                data = response.json()
                items = data.get("result", {}).get("items", [])
                for item in items:
                    channel = item.get("signing_channel", {})
                    if not channel or not channel.get("claim_id"):
                        continue
                    observed_tags = channel.get("value", {}).get("tags", [])
                    # Ignore tag-spammers
                    # The Odysee UI only lets you put 5 in. LBRY Desktop probably lets you do more,
                    # but if you're significantly above budget you're probably SEO spamming.
                    if len(observed_tags) > 15:
                        continue
                    yield (channel["claim_id"], channel)
                    if channel.get("timestamp") < oldestclaim:
                        oldestclaim = channel.get("timestamp")

        if stale_oldestclaim == oldestclaim:
            break
    return


def claim_search(handle, maxpages=20):
    """
    Calls the claim_search method in LBRY, attempting to find all claims for a handle (@foo:b)
    Returns a dict, indexed by claim_id, of all releases
    """
    assert maxpages > 0
    claims = {}
    for i in range(1, maxpages):
        payload = {
            "method": "claim_search",
            "params": {"channel": handle, "page_size": 50, "page": i}
            | common_claim_search_args,
        }
        response = requests.post(lbrynet_api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        items = data.get("result", {}).get("items", [])
        for item in items:
            if (
                item.get("value_type", "") in common_claim_search_bad_value_types
                or item.get("value", {}).get("stream_type", "")
                in common_claim_search_bad_stream_types
            ):
                continue
            claims[item["claim_id"]] = item
        if i == data.get("result", {}).get("total_pages", 1):
            break
    return claims
