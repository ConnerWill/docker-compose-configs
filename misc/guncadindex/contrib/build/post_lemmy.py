#! /usr/bin/env python3
import os
import requests

LEMMY_INSTANCE = os.environ.get("LEMMY_INSTANCE", "https://forum.guncadindex.com")
LEMMY_USERNAME = os.environ.get("LEMMY_USERNAME", "bot")
LEMMY_PASSWORD = os.environ.get("LEMMY_PASSWORD")
COMMUNITY_NAME = os.environ.get("LEMMY_COMMUNITY", "guncadindex")

_LOGO = "https://gitlab.com/guncad-index/index/-/raw/master/contrib/logo/guncad-index.png?ref_type=heads"

def get_jwt(username, password):
    url = f"{LEMMY_INSTANCE}/api/v3/user/login"
    resp = requests.post(url, json={
        "username_or_email": username,
        "password": password
    })
    resp.raise_for_status()
    return resp.json()["jwt"]

def get_community_id(community_name, token):
    url = f"{LEMMY_INSTANCE}/api/v3/community"
    resp = requests.get(url, params={"name": community_name},
                        headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    data = resp.json().get("community_view", {})
    if data["community"]:
        return data["community"]["id"]
    raise ValueError(f"Community '{community_name}' not found")

def main():
    # Lease token
    token = get_jwt(LEMMY_USERNAME, LEMMY_PASSWORD)

    tag = os.environ.get('CI_COMMIT_TAG', 'Unknown Tag')
    changelog = os.environ.get('CI_COMMIT_TAG_MESSAGE', '* No release notes for this tag!')
    url = f"https://gitlab.com/guncad-index/index/-/releases/{tag}" if tag != "Unknown Tag" else "https://gitlab.com/guncad-index/index"

    post_body = f"""
# GunCAD Index {tag} Released

**Changes should be live in production within 24 hours**

---

{changelog}

---

{url}

@TheShittinator@forum.guncadindex.com
"""

    community_id = get_community_id(COMMUNITY_NAME, token)

    post_url = f"{LEMMY_INSTANCE}/api/v3/post"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "community_id": community_id,
        "name": f"GunCAD Index {tag} Released",
        "body": post_body,
        "custom_thumbnail": _LOGO,
        "nsfw": False
    }

    resp = requests.post(post_url, json=payload, headers=headers)
    if resp.status_code == 200:
        print("Post sent successfully!")
    else:
        print(f"Failed to post: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
