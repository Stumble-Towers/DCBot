import asyncio
import os
from bot import DiscordBot
from dotenv import load_dotenv

load_dotenv()

async def main():
    bot = DiscordBot()
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN is missing. Check your .env file.")
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
