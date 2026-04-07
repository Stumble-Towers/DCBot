import discord
import aiohttp
from discord import app_commands
from discord.ext import commands
from utils.oauth_store import get_token


OAUTH_URL = (
    "https://discord.com/oauth2/authorize"
    "?client_id=1490798166302265445"
    "&response_type=code"
    "&redirect_uri=https%3A%2F%2Fhyperlowmc.net%2Fcallback"
    "&scope=identify+connections"
)


class SocialLink(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="checksocial", description="Check a user's linked YouTube channel.")
    @app_commands.describe(user="The user to check — leave empty to check yourself")
    async def checksocial(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None
    ):
        await interaction.response.defer(ephemeral=True)

        target = user or interaction.user

        token = await get_token(target.id)

        if not token:
            embed = discord.Embed(
                title="🔗 Link your YouTube",
                description=(
                    f"{target.mention} hasn't linked their account yet.\n\n"
                    f"To link your YouTube account, click the button below and authorize with Discord."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Only your connections are read — nothing else.")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Link your account",
                url=OAUTH_URL,
                style=discord.ButtonStyle.link,
                emoji="🔗"
            ))

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            return

        youtube_handle = await fetch_youtube(token)

        if not youtube_handle:
            embed = discord.Embed(
                title="No YouTube found",
                description=f"{target.mention} has linked their Discord but has no YouTube channel connected.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📺 YouTube Channel",
            description=f"{target.mention}'s linked YouTube channel is **{youtube_handle}**",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Channel",
            value=f"[{youtube_handle}](https://youtube.com/{youtube_handle})"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def fetch_youtube(access_token: str) -> str | None:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v10/users/@me/connections",
            headers=headers
        ) as resp:
            if resp.status != 200:
                return None
            connections = await resp.json()

    for conn in connections:
        if conn["type"] == "youtube":
            return f"@{conn['name']}"

    return None


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialLink(bot))