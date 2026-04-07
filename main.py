import asyncio
import uvicorn
import os
from bot import DiscordBot
from utils.oauth_callback import app as fastapi_app
from dotenv import load_dotenv

load_dotenv()

async def main():
    bot = DiscordBot()

    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    await asyncio.gather(
        bot.start(os.getenv("DISCORD_BOT_TOKEN")),
        server.serve()
    )

asyncio.run(main())