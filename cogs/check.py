import asyncio
import re
import aiohttp
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.oauth_store import get_token
from utils.youtube_api import get_channel_info, get_shorts_stats

# ── Constants ──────────────────────────────────────────────────────────────────

OAUTH_URL = (
    "https://discord.com/oauth2/authorize"
    "?client_id=1490798166302265445"
    "&response_type=code"
    "&redirect_uri=https%3A%2F%2Fhyperlowmc.net%2Fcallback"
    "&scope=identify+connections"
)

# Ordered highest → lowest so the first match wins
TIERS = [
    {"name": "OG",   "emoji": "👑", "color": 0xFFD700, "subs": 2000, "vpv": 4500, "spw": 5},
    {"name": "Goat", "emoji": "🐐", "color": 0x9B59B6, "subs": 1000, "vpv": 2000, "spw": 4},
    {"name": "Boss", "emoji": "💼", "color": 0xE67E22, "subs":  500, "vpv": 1000, "spw": 3},
    {"name": "Pro",  "emoji": "⭐", "color": 0x3498DB, "subs":  100, "vpv":  500, "spw": 2},
]

POLL_INTERVAL = 5    # seconds between token polls
POLL_TIMEOUT  = 300  # give up after 5 minutes

# ── Helpers ────────────────────────────────────────────────────────────────────

def _iso_duration_to_seconds(iso: str) -> int:
    """PT1M30S → 90.  Returns 9999 on parse failure so non-shorts are excluded."""
    m = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 9999
    d, h, mi, s = (int(v or 0) for v in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


async def _fetch_youtube_handle(access_token: str) -> str | None:
    """Returns '@handle' of the YouTube connection on the user's Discord account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v10/users/@me/connections",
            headers=headers,
        ) as resp:
            if resp.status != 200:
                return None
            connections = await resp.json()
    for conn in connections:
        if conn["type"] == "youtube":
            return f"@{conn['name']}"
    return None



def _evaluate_tier(subs: int, avg_views: float, per_week: float) -> dict | None:
    """Returns the highest tier the user qualifies for, or None."""
    for tier in TIERS:  # already sorted highest → lowest
        if subs >= tier["subs"] and avg_views >= tier["vpv"] and per_week >= tier["spw"]:
            return tier
    return None


def _build_requirements_field(subs: int, avg_views: float, per_week: float) -> str:
    """Builds the ✅/❌ checklist for all tiers."""
    lines = []
    for t in reversed(TIERS):  # show lowest tier at top for readability
        cs = "✅" if subs      >= t["subs"] else "❌"
        cv = "✅" if avg_views >= t["vpv"]  else "❌"
        cw = "✅" if per_week  >= t["spw"]  else "❌"
        lines.append(
            f"{t['emoji']} **{t['name']}** — "
            f"{cs} {t['subs']:,} subs · "
            f"{cv} {t['vpv']:,} views/short · "
            f"{cw} {t['spw']} shorts/week"
        )
    return "\n".join(lines)


# ── Cog ────────────────────────────────────────────────────────────────────────

class Check(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="check",
        description="Check your YouTube tier on this server.",
    )
    async def check(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        user = interaction.user

        # ── 1. OAuth token check ─────────────────────────────────────────────
        token = await get_token(user.id)
        status_msg = None  # we'll hold a reference to edit later

        if not token:
            link_embed = discord.Embed(
                title="🔗 Link your account first",
                description=(
                    "Click the button below and authorize with Discord.\n\n"
                    "The bot will **automatically continue** once you've linked — "
                    "no need to run `/check` again."
                ),
                color=discord.Color.blurple(),
            )
            link_embed.set_footer(text="⏳ Waiting… times out in 5 minutes")

            link_view = discord.ui.View()
            link_view.add_item(discord.ui.Button(
                label="Link your account",
                url=OAUTH_URL,
                style=discord.ButtonStyle.link,
                emoji="🔗",
            ))

            # Store the message so we can edit it in-place
            status_msg = await interaction.followup.send(
                embed=link_embed, view=link_view, ephemeral=False
            )

            # Poll until the OAuth callback writes the token
            elapsed = 0
            while elapsed < POLL_TIMEOUT:
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
                token = await get_token(user.id)
                if token:
                    break

            if not token:
                await status_msg.edit(
                    embed=discord.Embed(
                        title="⏰ Timed out",
                        description="You didn't link your account in time. Run `/check` again.",
                        color=discord.Color.red(),
                    ),
                    view=None,
                )
                return

            # Tell the user we found the token and are continuing
            await status_msg.edit(
                embed=discord.Embed(
                    title="✅ Account linked!",
                    description="Fetching your YouTube stats now…",
                    color=discord.Color.green(),
                ),
                view=None,
            )

        # ── 2. YouTube handle via Discord connections ────────────────────────
        handle = await _fetch_youtube_handle(token)
        if not handle:
            err = discord.Embed(
                title="No YouTube Connected",
                description=(
                    "Your Discord is linked, but no YouTube channel is attached.\n"
                    "Go to **Discord Settings → Connections** and add your YouTube."
                ),
                color=discord.Color.orange(),
            )
            if status_msg:
                await status_msg.edit(embed=err, view=None)
            else:
                await interaction.followup.send(embed=err, ephemeral=False)
            return

        # ── 3. Channel info (subs, total views, etc.) ────────────────────────
        try:
            channel_data = await get_channel_info(handle)
        except ValueError as e:
            await interaction.followup.send(
                embed=discord.Embed(title="⚙️ Config Error", description=str(e), color=discord.Color.orange()),
                ephemeral=False,
            )
            return
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(title="❌ YouTube API Error", description=f"`{e}`", color=discord.Color.red()),
                ephemeral=False,
            )
            return

        if not channel_data:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔍 Channel Not Found",
                    description=f"No channel found for **{handle}**.",
                    color=discord.Color.yellow(),
                ),
                ephemeral=False,
            )
            return

        stats         = channel_data.get("statistics", {})
        snippet       = channel_data.get("snippet", {})
        channel_id    = channel_data.get("id", "")
        channel_title = snippet.get("title", "Unknown")
        sub_count     = int(stats.get("subscriberCount", 0))
        hidden_subs   = stats.get("hiddenSubscriberCount", False)
        thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
        channel_url   = f"https://www.youtube.com/channel/{channel_id}"

        # ── 4. Shorts stats ──────────────────────────────────────────────────
        shorts_data = await get_shorts_stats(channel_id)
        avg_views   = shorts_data["avg_views"] if shorts_data else 0.0
        per_week    = shorts_data["per_week"]  if shorts_data else 0.0

        # ── 5. Evaluate tier ─────────────────────────────────────────────────
        tier = _evaluate_tier(sub_count, avg_views, per_week)

        if tier:
            embed = discord.Embed(
                title=f"{tier['emoji']}  {tier['name']} Tier",
                description=(
                    f"{user.mention}, your channel "
                    f"**[{channel_title}]({channel_url})** "
                    f"qualifies for **{tier['name']} Tier**! 🎉"
                ),
                color=tier["color"],
            )
        else:
            embed = discord.Embed(
                title="📊 No Tier Yet",
                description=(
                    f"{user.mention}, your channel "
                    f"**[{channel_title}]({channel_url})** "
                    "doesn't meet any tier requirements yet. Keep going! 💪"
                ),
                color=discord.Color.greyple(),
            )

        embed.add_field(
            name="👥 Subscribers",
            value="*Hidden by owner*" if hidden_subs else f"{sub_count:,}",
            inline=True,
        )
        embed.add_field(
            name="📈 Avg Views / Short",
            value=f"{avg_views:,.0f}" if shorts_data else "*No shorts found*",
            inline=True,
        )
        embed.add_field(
            name="📅 Shorts / Week",
            value=f"{per_week:.1f}" if shorts_data else "*No shorts found*",
            inline=True,
        )
        embed.add_field(
            name="📋 Tier Requirements",
            value=_build_requirements_field(sub_count, avg_views, per_week),
            inline=False,
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        embed.set_footer(
            text=f"YouTube Data API v3  •  Checked {shorts_data['sample']} shorts"
            if shorts_data else "YouTube Data API v3",
        )

        await interaction.followup.send(embed=embed, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Check(bot))