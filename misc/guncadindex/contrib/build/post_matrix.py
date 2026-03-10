#! /usr/bin/env python3
import asyncio
import os
from nio import AsyncClient, RoomMessageText
import markdown

async def send_message():
    client = AsyncClient("https://matrix.org", os.environ.get("MATRIX_USER", "@guncadindex-bot:matrix.org"))
    if os.environ.get("MATRIX_PASSWORD"):
        print("Using password from environment")
        print(await client.login(os.environ.get("MATRIX_PASSWORD")))
    elif os.environ.get("MATRIX_ACCESS_TOKEN"):
        print("Using access token from environment")
        client.access_token = os.environ.get("MATRIX_ACCESS_TOKEN")
    else:
        print("No method of credentials provided")
        exit(1)
    room_id = os.environ.get("MATRIX_ROOM_ID")

    print(f"Sending to room \"{room_id}\" using token starting with \"{client.access_token[0]}\"")

    tag = os.environ.get('CI_COMMIT_TAG', 'Unknown Tag')
    changelog = os.environ.get('CI_COMMIT_TAG_MESSAGE', '* No release notes for this tag! Bitch at the devs!')
    url = f"https://gitlab.com/guncad-index/index/-/releases/{tag}" if tag != "Unknown Tag" else "No URL for this release"

    # Basic markdown message
    message = f"""
# GunCAD Index {tag} Released

**Changes should be live in production within 24 hours**

---

{changelog}

---

{url}
"""
    # Mark markdown up to HTML for rich clients
    html_message = markdown.markdown(message, extensions=['extra'])

    # Send formatted message
    try:
        await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message,  # Plain text fallback
                "format": "org.matrix.custom.html",
                "formatted_body": html_message
            }
        )
        print("Message sent successfully")
    except Exception as e:
        print(f"Failed to send message: {e}")
        exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(send_message())
