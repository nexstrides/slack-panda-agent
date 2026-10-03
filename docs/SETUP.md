# PandaAgent Setup Guide

Complete setup instructions for getting PandaAgent running locally.

## Prerequisites

- Go 1.21+
- Python 3.10+
- Node.js 18+
- Slack Workspace with admin access
- Anthropic Claude API key (for history-aware answers)

## Step 1: Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create an app from scratch named `PandaAgent`
3. Select your workspace

### OAuth & Permissions

Add these **Bot Token Scopes**, then reinstall the app:

- `app_mentions:read`
- `chat:write`
- `commands`
- `channels:history`
- `channels:read`
- `groups:history`
- `groups:read`
- `im:history`
- `im:read`
- `im:write`
- `mpim:history`
- `mpim:read`
- `users:read`

Invite the bot into each channel it should study: `/invite @PandaAgent`

### Event Subscriptions

Enable events and set Request URL to:

`https://your-public-url/slack/events`

Subscribe to bot events:

- `app_mention`
- `message.channels`
- `message.groups`
- `message.im`
- `message.mpim`

### App Home

Under **App Home**, enable **Messages Tab** and allow users to send DM messages. That is required for questions in a direct channel.

### Slash Commands

Create `/panda` with Request URL:

`https://your-public-url/slack/commands`

Slack cannot reach `localhost`. Use a tunnel such as `ngrok http 3000` and put that HTTPS URL in the Slack app settings.

## Step 2: Local Setup

```bash
cp .env.example .env
```

Fill in `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and `CLAUDE_API_KEY`.

## Step 3: Run Services

Docker:

```bash
docker compose up --build
```

Or run each service locally as in the root README.

## Step 4: Test

- Mention the bot in a channel: `@PandaAgent what should I do this week?`
- Open a DM with the bot and ask the same question. The reply stays in that DM.
- Slash command: `/panda what is outstanding from #eng?`

## Troubleshooting

- No reply: Slack Request URLs must be the public HTTPS tunnel, not localhost
- Empty answers: invite the bot to the channels, add history scopes, and reinstall the app
- Signature errors: `SLACK_SIGNING_SECRET` does not match the Slack app
- Weak answers: set `CLAUDE_API_KEY`
