import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Called automatically before the bot logs in — loads cogs and syncs slash commands."""
        await self.load_extension("cogs.youtube")
        await self.load_extension("cogs.SocialLink")
        synced = await self.tree.sync()
        print(f"[Bot] Synced {len(synced)} slash command(s).")

    async def on_ready(self):
        print(f"[Bot] Logged in as {self.user} (ID: {self.user.id})")
        print(f"[Bot] Connected to {len(self.guilds)} guild(s).")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="YouTube channels"
            )
        )

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global slash command error handler."""
        msg = f"An unexpected error occurred: `{error}`"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
