# PandaAgent Architecture

## System Overview

PandaAgent is a multi-service Slack AI agent with the following components:

- Slack workspace
- Go Slack bot
- Python FastAPI service
- React frontend
- Claude AI integration

## Component Details

### Slack Bot (Go)
- Receives events and slash commands
- Verifies Slack signatures
- Echoes messages for the MVP
- Sends responses to Slack

### Python API (FastAPI)
- Exposes `/health`, `/echo`, `/ask-claude`, `/process-message`
- Integrates with Anthropic Claude API
- Runs business logic

### Web Frontend (React + TS)
- Landing page
- API health status
- Message testing UI

## Flow

1. User mentions bot in Slack
2. Slack sends event to `/slack/events`
3. Go bot validates the request
4. Go bot replies with an echo message
5. Python API is ready to route more advanced logic
6. Future steps: add Claude prompts and persistent memory
