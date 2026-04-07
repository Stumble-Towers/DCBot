import os
import aiohttp
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from utils.oauth_store import save_token

app = FastAPI()

CLIENT_ID     = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = "https://hyperlowmc.net/callback"


@app.get("/callback")
async def callback(code: str = None, error: str = None, error_description: str = None):

    if error:
        return RedirectResponse(
            url=f"/callback.html?error={error}&error_description={error_description or ''}"
        )

    if not code:
        return RedirectResponse(url="/callback.html?error=missing_code")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as resp:
            token_data = await resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(
                url="/callback.html?error=token_exchange_failed"
            )

        async with session.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        ) as resp:
            user_data = await resp.json()

    user_id = int(user_data["id"])
    save_token(user_id, access_token)

    return RedirectResponse(url="/callback.html")