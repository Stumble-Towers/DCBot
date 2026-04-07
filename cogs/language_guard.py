# cogs/language_guard.py
import discord
from discord.ext import commands
import aiohttp
import os

EN_CHANNEL_ID = 1485680001323110491
DE_CHANNEL_ID = 1486458108858601603

WATCHED_CHANNELS = {EN_CHANNEL_ID, DE_CHANNEL_ID}

DETECT_URL = "https://ws.detectlanguage.com/v3/detect"


class LanguageGuard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._api_key = os.getenv("DETECT_LANGUAGE_API_KEY")

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _detect_language(self, session: aiohttp.ClientSession, text: str) -> str | None:
        """Returns the ISO 639-1 language code (e.g. 'en', 'de') or None on failure."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with session.post(DETECT_URL, json={"q": text}, headers=headers) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                detections = data.get("data", {}).get("detections", [])
                if not detections:
                    return None
                return detections[0].get("language")
        except aiohttp.ClientError:
            return None

    @staticmethod
    def _error_embed(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red(),
        )
        embed.set_footer(text="Your message was removed.")
        return embed

    @staticmethod
    async def _dm_user(user: discord.Member | discord.User, embed: discord.Embed) -> None:
        """Attempt to DM the user; silently skip if they block DMs."""
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass

    # ------------------------------------------------------------------ #
    #  Listener                                                            #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        print(f"[LG] on_message fired | author={message.author} | channel={message.channel.id} | content={repr(message.content)}")
        # Ignore bots and messages outside the watched channels
        if message.author.bot:
            return
        if message.channel.id not in WATCHED_CHANNELS:
            return
        # Skip messages with no detectable text (images-only, stickers, etc.)
        if not message.content.strip():
            return

        print(f"[LG] Passed guards, detecting language...")

            try:
        async with aiohttp.ClientSession() as session:
            detected = await self._detect_language(session, message.content)
        print(f"[LG] Detected: {detected}")
    except Exception as e:
        print(f"[LG] EXCEPTION: {type(e).__name__}: {e}")
        return

        channel_id = message.channel.id

        # ── English channel ──────────────────────────────────────────────
        if channel_id == EN_CHANNEL_ID:
            if detected == "en":
                return  # ✅ Correct language — nothing to do

            await message.delete()

            if detected == "de":
                embed = self._error_embed(
                    title="❌ Wrong Language",
                    description=(
                        f"This channel is **English only**.\n"
                        f"Please send your message in <#{DE_CHANNEL_ID}>."
                    ),
                )
            else:
                embed = self._error_embed(
                    title="❌ Wrong Language",
                    description=(
                        "This channel is **English only**.\n"
                        "Please write your message in **English**."
                    ),
                )
            await self._dm_user(message.author, embed)

        # ── German channel ───────────────────────────────────────────────
        elif channel_id == DE_CHANNEL_ID:
            if detected == "de":
                return  # ✅ Correct language — nothing to do

            await message.delete()

            if detected == "en":
                embed = self._error_embed(
                    title="❌ Falsche Sprache",
                    description=(
                        f"Dieser Kanal ist **nur auf Deutsch**.\n"
                        f"Bitte sende deine Nachricht in <#{EN_CHANNEL_ID}>."
                    ),
                )
            else:
                embed = self._error_embed(
                    title="❌ Falsche Sprache",
                    description=(
                        "Dieser Kanal ist **nur auf Deutsch**.\n"
                        "Bitte schreibe deine Nachricht auf **Deutsch**."
                    ),
                )
            await self._dm_user(message.author, embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LanguageGuard(bot))