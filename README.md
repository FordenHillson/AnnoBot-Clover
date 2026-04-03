# AnnoBot - Discord Auto-Announcement Bot

A Discord bot with a web dashboard for managing scheduled auto-announcements.

## Features

- Create, edit, delete scheduled announcements
- **Weekly** schedule (e.g., `mon,wed,fri 14:00`)
- **Custom cron** schedule (e.g., `0 14 * * 1,3,5`)
- Auto-edits existing messages instead of spamming new ones
- Password-protected web dashboard
- Deploy-ready for Replit, Render, or any Python host

## Setup

### 1. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to **Bot** tab, create bot, copy the **Token**
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Go to **OAuth2 > URL Generator**, select scopes: `bot`, permissions: `Send Messages`, `Manage Messages`
6. Use the generated URL to invite the bot to your server

### 2. Get Channel ID

1. In Discord, go to **User Settings > Advanced > Developer Mode** (enable it)
2. Right-click any channel and select **Copy Channel ID**

### 3. Local Development

```bash
# Clone and setup
git clone <your-repo>
cd AnnoBot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your values

# Run
python bot.py
```

The dashboard will be available at `http://localhost:10000`

### 4. Deploy to Replit

1. Go to https://replit.com and click **Create Repl**
2. Select **Import from GitHub** and choose your repo
3. Go to **Secrets** (lock icon in Tools) and add:
   - `DISCORD_TOKEN` - Your Discord bot token
   - `DASHBOARD_PASSWORD` - Your dashboard password
   - `TIMEZONE` - Set to `Asia/Bangkok`
4. Click **Run**
5. The dashboard will be available in the Webview panel

> **Note**: Free Replit accounts sleep after inactivity. Use [UptimeRobot](https://uptimerobot.com) to ping your Repl URL every 5 minutes to keep it alive. The dashboard URL is shown in the Webview panel when running.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token (required) | - |
| `DASHBOARD_PASSWORD` | Web dashboard password | `admin` |
| `PORT` | Port for web dashboard | `10000` |
| `TIMEZONE` | Timezone for schedules | `UTC` |
| `DATABASE_PATH` | SQLite database file path | `annobot.db` |

## Dashboard Usage

### Schedule Formats

**Weekly**: `days time`
```
mon,wed,fri 14:00
tue,thu 09:30
mon 18:00
```

**Cron**: `minute hour day month day_of_week`
```
0 14 * * 1,3,5        # Mon/Wed/Fri at 2:00 PM
30 9 * * 1-5          # Mon-Fri at 9:30 AM
0 0 1 * *             # First of every month at midnight
*/30 * * * *          # Every 30 minutes
```

### Bot Commands

- `!sync` - Reload all scheduled jobs from database (admin only)

## Project Structure

```
AnnoBot/
├── bot.py                 # Main entry (Discord bot + Flask)
├── database.py            # SQLite database operations
├── scheduler.py           # APScheduler job management
├── requirements.txt       # Python dependencies
├── Procfile               # Render deployment config
├── .env.example           # Environment variables template
├── templates/
│   ├── base.html          # Base layout
│   ├── login.html         # Login page
│   ├── dashboard.html     # Main dashboard
│   └── announcement_form.html  # Create/edit form
└── static/
    └── style.css          # Dashboard styles
```
