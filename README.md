# Turnitin Status Telegram Bot

A Telegram bot that monitors Turnitin's maintenance status and sends notifications when it becomes active.

## Features
- 📊 Check current Turnitin status
- 🔔 Subscribe to get notified when Turnitin becomes active
- 🔕 Unsubscribe from notifications
- 🔄 Real-time status monitoring (every 1 second)

## Commands
- `/start` - Start the bot and see menu
- `/status` - Check current Turnitin status
- `/subscribe` - Subscribe to notifications
- `/unsubscribe` - Unsubscribe from notifications

## Deployment

### Railway (Recommended)
1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project → Deploy from GitHub
4. Select this repository
5. Railway will auto-detect and deploy

### Render
1. Push to GitHub
2. Create a new **Background Worker** on Render
3. Connect your repository

### Local
```bash
pip install -r requirements.txt
python3 turnitin_bot.py
```

## Environment
The bot token is embedded in the code. For production, consider using environment variables.
