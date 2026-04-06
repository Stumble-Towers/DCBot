# 🤖 Discord Bot Base — Python

A clean, production-ready Discord bot base built with **discord.py 2.x**, using a **cog-based architecture** and **slash commands**. Designed to be extended — drop in new cogs and go.

***

## 📁 Project Structure

```
discord-bot/
├── main.py               # Entry point — run this
├── bot.py                # Core bot class (setup, events, error handling)
├── cogs/                 # One file per feature area
│   ├── __init__.py
│   └── youtube.py        # Example cog
├── utils/                # Shared helpers and API wrappers
│   ├── __init__.py
│   └── youtube_api.py    # Example utility
├── .env                  # Your secrets — never commit this
├── .env.example          # Template to copy from
├── .gitignore
├── requirements.txt
└── README.md
```

***

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 3. Run

```bash
python main.py
```

***

## 🧠 How the Base Works

### `main.py`
Minimal entry point. Loads `.env`, creates the bot instance, and calls `bot.start(token)` inside `asyncio.run()`. Nothing else lives here.

### `bot.py` — The `DiscordBot` class
Extends `commands.Bot`. The three key parts:

- **`__init__`** — Sets up `Intents` and the command prefix.
- **`setup_hook`** — Called automatically before login. This is where cogs are loaded via `load_extension()` and slash commands are globally synced via `tree.sync()`.
- **`on_ready`** — Fires when the bot connects. Logs guild count and sets the presence status.
- **`on_app_command_error`** — Global slash command error handler. Catches anything not handled inside a cog and replies ephemerally so errors are never silent.

### `cogs/` — Feature modules
Each cog is a `commands.Cog` subclass in its own file. Cogs group related commands and listeners together. They are loaded dynamically by `setup_hook` — adding a cog is just two lines.

### `utils/` — Shared logic
The `utils/` folder is for code that **supports** your cogs but isn't a command itself. The rule of thumb: if two or more cogs would need the same function, it belongs in `utils/`.

Common things that live here:

- **API wrappers** — async functions that call external services (YouTube, Spotify, weather APIs, etc.). Keeps HTTP logic out of your cog files.
- **Helper functions** — formatting numbers, parsing strings, building embeds, calculating timestamps.
- **Constants** — colour codes, emoji maps, rate limit values, shared configuration that multiple cogs reference.
- **Validators** — input checking logic (e.g. is this a valid URL? is this number in range?) so cogs stay readable.

#### Example

Instead of writing the same HTTP call in three different cogs:

```python
# utils/youtube_api.py
async def get_channel_info(channel_query: str) -> dict | None:
    ...
```

Any cog can then import and use it cleanly:

```python
# cogs/youtube.py
from utils.youtube_api import get_channel_info
```

This keeps cogs thin, makes utilities easy to test in isolation, and means you only need to update API logic in one place.

***

## ➕ Adding a New Command

### 1. Create a cog file

```python
# cogs/example.py
import discord
from discord import app_commands
from discord.ext import commands

class Example(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Replies with Pong!")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Example(bot))
```

### 2. Register it in `bot.py`

Inside `setup_hook`, add:

```python
await self.load_extension("cogs.example")
```

That's it. The slash command syncs automatically on next startup.

***

## 🔒 Ephemeral Replies

Pass `ephemeral=True` to any response to make it visible **only to the user who ran the command**. It appears inline in the channel as *"Only you can see this"* — no DM required.

```python
await interaction.response.send_message("Secret!", ephemeral=True)
```

For commands that need async work before replying (e.g. API calls), defer first:

```python
await interaction.response.defer(ephemeral=True)
# ... do work ...
await interaction.followup.send("Result", ephemeral=True)
```

***

## 🛡️ Environment Variables

All secrets are read from `.env` via `python-dotenv`. The `.gitignore` already excludes `.env` — use `.env.example` as the source of truth for what variables are expected. Never hardcode tokens or keys in source files.

***

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `discord.py >= 2.3` | Discord API, slash commands, cog system |
| `python-dotenv >= 1.0` | Loads `.env` into `os.environ` |
| `aiohttp >= 3.9` | Async HTTP for external API calls |

Install all at once:

```bash
pip install -r requirements.txt
```