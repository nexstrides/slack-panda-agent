# Python API Service

Handles business logic, Claude AI integration, and message processing.

## Features

- FastAPI web framework
- Slack history backfill and SQLite store
- History-aware answers via Claude
- Health checks

## Setup

```bash
cd services/python-api

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

```bash
python app.py
```

The service will listen on port 8000 by default.

## Endpoints

- `GET /` - API overview
- `GET /health` - Health check
- `POST /ask` - Answer a question from stored Slack history
- `POST /history/ingest` - Store a Slack message
- `POST /echo` - Echo endpoint (validation)

## Configuration

Requires environment variables:
- `CLAUDE_API_KEY` - Anthropic API key
- `CLAUDE_MODEL` - Claude model (default: claude-3-5-sonnet-20241022)
- `SLACK_BOT_TOKEN` - used to backfill channel history
- `PORT` - Port to listen on (default: 8000)
