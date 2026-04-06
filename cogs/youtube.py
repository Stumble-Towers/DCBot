import discord
from discord import app_commands
from discord.ext import commands
from utils.youtube_api import get_channel_info


class YouTube(commands.Cog):
    """Cog that provides YouTube channel lookup commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # /checkchannel <channel>
    # ------------------------------------------------------------------
    @app_commands.command(
        name="checkchannel",
        description="Check the subscriber count (and more) of a YouTube channel.",
    )
    @app_commands.describe(
        channel="YouTube handle (@MrBeast), channel name, or channel ID"
    )
    async def checkchannel(self, interaction: discord.Interaction, channel: str):
        """
        Replies with an ephemeral embed visible only to the caller.
        ephemeral=True means it shows as a private message inside the channel —
        NOT sent to DMs; only the invoking user can see it.
        """
        # Defer immediately so we have up to 15 min to respond.
        await interaction.response.defer(ephemeral=True)

        try:
            channel_data = await get_channel_info(channel)
        except ValueError as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⚙️ Configuration Error",
                    description=str(e),
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
            return
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ API Error",
                    description=f"Failed to contact the YouTube API:\n`{e}`",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        if not channel_data:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔍 Channel Not Found",
                    description=(
                        f"No YouTube channel found for **`{channel}`**.\n\n"
                        "Try using:\n"
                        "• A handle: `@MrBeast`\n"
                        "• A channel ID: `UCX6OQ3DkcsbYNE6H8uQQuVA`"
                    ),
                    color=discord.Color.yellow(),
                ),
                ephemeral=True,
            )
            return

        # ── Parse the API response ──────────────────────────────────────
        stats = channel_data.get("statistics", {})
        snippet = channel_data.get("snippet", {})

        hidden_subs: bool = stats.get("hiddenSubscriberCount", False)
        sub_count: int = int(stats.get("subscriberCount", 0))
        video_count: int = int(stats.get("videoCount", 0))
        view_count: int = int(stats.get("viewCount", 0))

        channel_title: str = snippet.get("title", "Unknown Channel")
        raw_desc: str = snippet.get("description", "")
        short_desc: str = (raw_desc[:200] + "…") if len(raw_desc) > 200 else raw_desc
        thumbnail_url: str = (
            snippet.get("thumbnails", {}).get("high", {}).get("url", "")
        )
        channel_id: str = channel_data.get("id", "")
        channel_url: str = f"https://www.youtube.com/channel/{channel_id}"

        # ── Build the embed ─────────────────────────────────────────────
        embed = discord.Embed(
            title=f"📺  {channel_title}",
            url=channel_url,
            color=0xFF0000,  # YouTube red
        )

        embed.add_field(
            name="👥 Subscribers",
            value="*Hidden by owner*" if hidden_subs else f"{sub_count:,}",
            inline=True,
        )
        embed.add_field(name="🎬 Videos", value=f"{video_count:,}", inline=True)
        embed.add_field(name="👁️ Total Views", value=f"{view_count:,}", inline=True)

        if short_desc:
            embed.add_field(name="📝 Description", value=short_desc, inline=False)

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        embed.set_footer(text="YouTube Data API v3  •  Only you can see this message")

        await interaction.followup.send(embed=embed, ephemeral=True)


# Required by discord.py's cog loader
async def setup(bot: commands.Bot):
    await bot.add_cog(YouTube(bot))
