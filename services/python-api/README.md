# Python API Service

Handles business logic, Claude AI integration, and message processing.

## Features

- FastAPI web framework
- Claude AI integration
- Message processing
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
- `POST /echo` - Echo endpoint (validation)
- `POST /ask-claude` - Send message to Claude
- `POST /process-message` - Process Slack message

## Configuration

Requires environment variables:
- `CLAUDE_API_KEY` - Anthropic API key
- `CLAUDE_MODEL` - Claude model (default: claude-3-5-sonnet-20241022)
- `PORT` - Port to listen on (default: 8000)
