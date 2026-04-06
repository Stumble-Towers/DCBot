# 🤖 Discord Bot Base — Python

A clean, cog-based Discord bot built with **discord.py 2.x** and slash commands.

## ✨ Features

| Command | Description |
|---|---|
| `/checkchannel <channel>` | Shows subscriber count, video count, and total views of a YouTube channel — visible **only to you** (ephemeral) |

---

## 📁 Project Structure

```
discord-bot/
├── main.py               # Entry point — run this
├── bot.py                # Bot class, setup_hook, on_ready
├── cogs/
│   ├── __init__.py
│   └── youtube.py        # /checkchannel slash command
├── utils/
│   ├── __init__.py
│   └── youtube_api.py    # Async YouTube Data API v3 wrapper
├── .env                  # Your secrets (never commit this!)
├── .env.example          # Template to copy
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup

### 1. Clone & install dependencies

```bash
git clone <your-repo>
cd discord-bot
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

#### Getting a Discord Bot Token
1. Go to https://discord.com/developers/applications
2. Create a new Application → Bot tab → Reset Token
3. Enable **Message Content Intent** under Privileged Gateway Intents
4. Under OAuth2 → URL Generator, tick `bot` + `applications.commands` scopes
5. Paste the generated invite link into your browser to add the bot to your server

#### Getting a YouTube API Key
1. Go to https://console.cloud.google.com/
2. Create a project → Enable **YouTube Data API v3**
3. Credentials → Create Credentials → API Key

### 3. Run the bot

```bash
python main.py
```

You should see:
```
[Bot] Synced 1 slash command(s).
[Bot] Logged in as YourBot#1234 (ID: 123456789)
[Bot] Connected to 1 guild(s).
```

---

## 🔧 Adding More Commands

1. Create a new file in `cogs/`, e.g. `cogs/moderation.py`
2. Follow the pattern in `cogs/youtube.py` (class extending `commands.Cog` + `async def setup(bot)`)
3. Register it in `bot.py` inside `setup_hook`:
   ```python
   await self.load_extension("cogs.moderation")
   ```

---

## 📝 Notes

- **Ephemeral replies** (`ephemeral=True`) appear as "Only you can see this" inside the channel — they are NOT sent to DMs. This is intentional: the response is private without cluttering the channel.
- Slash commands are globally synced on startup via `tree.sync()`. Changes may take up to 1 hour to propagate globally; for instant testing, use guild-scoped sync instead.
- The YouTube API has a free quota of **10,000 units/day**. Each `/checkchannel` call costs 3 units.
