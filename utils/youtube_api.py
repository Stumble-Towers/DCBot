import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


async def get_channel_info(channel_query: str) -> dict | None:
    """
    Fetches YouTube channel data by:
      1. Handle (e.g. @MrBeast or MrBeast)
      2. Channel ID (e.g. UCX6OQ3DkcsbYNE6H8uQQuVA)

    Returns the first matching channel item dict, or None if not found.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is not set in the .env file.")

    handle = channel_query.lstrip("@").strip()

    async with aiohttp.ClientSession() as session:
        # --- Pass 1: try forHandle (works for @handles) ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/channels",
            params={
                "part": "snippet,statistics",
                "forHandle": handle,
                "key": api_key,
            },
        ) as resp:
            data = await resp.json()
            if data.get("items"):
                return data["items"][0]

        # --- Pass 2: try as a raw channel ID ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/channels",
            params={
                "part": "snippet,statistics",
                "id": channel_query.strip(),
                "key": api_key,
            },
        ) as resp:
            data = await resp.json()
            if data.get("items"):
                return data["items"][0]

    return None
