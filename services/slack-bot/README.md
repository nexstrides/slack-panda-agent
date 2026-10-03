# Slack Bot Service (Go)

Handles all Slack event processing, command handling, and bot responses.

## Features

- Ingests channel and DM history for the Python agent
- Answers @mentions, DMs, and `/panda` in the same conversation
- Signature verification

## Setup

```bash
cd services/slack-bot
go mod download
```

## Running Locally

```bash
go run main.go
```

The service will listen on port 3000 by default.

## Endpoints

- `POST /slack/events` - Slack event subscriptions (mentions, messages)
- `POST /slack/commands` - Slash command handler
- `GET /health` - Health check

## Configuration

Requires environment variables:
- `SLACK_BOT_TOKEN` - Bot user token
- `SLACK_SIGNING_SECRET` - Signing secret for request verification
- `PYTHON_API_URL` - Python API base URL
- `SLACK_BOT_PORT` - Port to listen on (default: 3000)
