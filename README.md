# PandaAgent - Slack AI Agent

A multi-service Slack AI agent built with TypeScript, Go, Python, and Claude AI integration.

## Architecture

- **Frontend**: TypeScript/React landing & settings page
- **Slack Bot**: Go service handling Slack events and commands
- **Python API**: Business logic and Claude AI integration
- **Claude AI**: AI backbone for responses and intelligence

## Services

### 1. Web (TypeScript/React)
Landing page and settings dashboard for configuring the agent.

### 2. Slack Bot (Go)
- Handles Slack events (mentions, messages, commands)
- Processes slash commands
- Routes requests to Python API
- Sends notifications

### 3. Python API
- Claude AI integration
- Business logic and response generation
- Logging and analytics

## Quick Start

### Prerequisites
- Go 1.21+
- Python 3.10+
- Node.js 18+
- Slack Workspace with app permissions

### Environment Setup

```bash
cp .env.example .env
# Fill in your Slack Bot Token, Claude API Key, etc.
```

### Running Services

```bash
# Terminal 1: Go Slack Bot
cd services/slack-bot
go run main.go

# Terminal 2: Python API
cd services/python-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Terminal 3: Web Frontend
cd apps/web
npm install
npm run dev
```

## Configuration

See `.env.example` for required environment variables:
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `CLAUDE_API_KEY`
- `PYTHON_API_URL`
- `PORT`

## Features (MVP)

- ✅ Respond to mentions in Slack channels
- ✅ Process slash commands
- ✅ Echo responses (basic validation)
- ✅ Notification system for mentions
- ✅ Settings page (landing)
- 🔄 Claude AI integration (WIP)

## Project Structure

```
pandaagent/
├── apps/
│   └── web/                 # TypeScript landing & settings
├── services/
│   ├── slack-bot/          # Go Slack event handler
│   └── python-api/         # Python API with Claude
├── shared/
│   └── config/             # Shared configuration
├── docs/
│   └── ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Development

See individual service READMEs for detailed setup:
- [Web Setup](./apps/web/README.md)
- [Slack Bot Setup](./services/slack-bot/README.md)
- [Python API Setup](./services/python-api/README.md)

## License

MIT
