import os
import re
import aiohttp
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def _iso_duration_to_seconds(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 9999
    d, h, mi, s = (int(v or 0) for v in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


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
        # --- Pass 1: try forHandle ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/channels",
            params={
                "part":      "snippet,statistics",
                "forHandle": handle,
                "key":       api_key,
            },
        ) as resp:
            data = await resp.json()
            if data.get("items"):
                return data["items"][0]

        # --- Pass 2: try as raw channel ID ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/channels",
            params={
                "part": "snippet,statistics",
                "id":   channel_query.strip(),
                "key":  api_key,
            },
        ) as resp:
            data = await resp.json()
            if data.get("items"):
                return data["items"][0]

    return None


async def get_shorts_stats(channel_id: str) -> dict | None:
    """
    Returns {"avg_views": float, "per_week": float, "sample": int}
    or None if no shorts found / API error.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is not set in the .env file.")

    async with aiohttp.ClientSession() as session:
        # --- Pass 1: fetch recent video IDs ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/search",
            params={
                "part":       "id",
                "channelId":  channel_id,
                "type":       "video",
                "order":      "date",
                "maxResults": 50,
                "key":        api_key,
            },
        ) as resp:
            data = await resp.json()

        video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
        if not video_ids:
            return None

        # --- Pass 2: fetch duration + stats ---
        async with session.get(
            f"{YOUTUBE_API_BASE}/videos",
            params={
                "part": "contentDetails,statistics,snippet",
                "id":   ",".join(video_ids),
                "key":  api_key,
            },
        ) as resp:
            vdata = await resp.json()

    shorts = []
    for v in vdata.get("items", []):
        secs = _iso_duration_to_seconds(
            v.get("contentDetails", {}).get("duration", "PT999S")
        )
        if secs <= 60:
            shorts.append({
                "views":     int(v.get("statistics", {}).get("viewCount", 0)),
                "published": v.get("snippet", {}).get("publishedAt", ""),
            })

    if not shorts:
        return None

    avg_views    = sum(s["views"] for s in shorts) / len(shorts)
    cutoff       = datetime.now(timezone.utc) - timedelta(weeks=4)
    recent_count = sum(
        1 for s in shorts
        if s["published"] and
        datetime.fromisoformat(s["published"].replace("Z", "+00:00")) >= cutoff
    )

    return {"avg_views": avg_views, "per_week": recent_count / 4.0, "sample": len(shorts)}