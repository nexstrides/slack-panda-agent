# PandaAgent Setup Guide

Complete setup instructions for getting PandaAgent running locally.

## Prerequisites

- Go 1.21+
- Python 3.10+
- Node.js 18+
- Slack Workspace with admin access

## Step 1: Slack App Setup

1. Go to Slack API Dashboard
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: `PandaAgent`
5. Select your workspace
6. Click "Create App"

### Configure OAuth & Permissions

1. Go to "OAuth & Permissions"
2. Under "Scopes" → "Bot Token Scopes", add:
   - `app_mentions:read`
   - `chat:write`
   - `commands`
   - `channels:read`
   - `users:read`
3. Install to workspace
4. Copy the bot token

### Event Subscriptions

1. Enable events
2. Set Request URL to: `https://your-domain.com/slack/events`
3. Subscribe to `app_mention` and `message.channels`

### Slash Commands

1. Create `/panda`
2. Request URL: `https://your-domain.com/slack/commands`

## Step 2: Local Setup

```bash
cp .env.example .env
```

Fill in the values from your Slack app and Claude API key.

## Step 3: Run Services

### Slack Bot
```bash
cd services/slack-bot
go mod download
go run main.go
```

### Python API
```bash
cd services/python-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Web App
```bash
cd apps/web
npm install
npm run dev
```

## Step 4: Test

- Open `http://localhost:3001`
- Mention the bot in Slack: `@PandaAgent hello`
- Use slash command: `/panda hello`

## Troubleshooting

- Check `.env` values
- Ensure Slack app is installed in workspace
- Verify ngrok tunnel if using local webhooks
