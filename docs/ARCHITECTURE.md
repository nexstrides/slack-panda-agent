# PandaAgent Architecture

## System Overview

PandaAgent is a Slack teammate that studies workspace chat history and answers questions in the same channel where you ask, including DMs.

- Slack workspace
- Go Slack bot
- Python FastAPI service with a local history store
- React frontend
- Claude for answers grounded in that history

## Flow

1. Slack sends message, mention, and slash-command events to the Go bot.
2. The bot verifies the request, stores the message with the Python API, and returns 200 quickly.
3. On startup, Python also backfills recent history from channels the bot can read.
4. If the user asked a question (`@PandaAgent`, DM, or `/panda`), Python retrieves matching history (who, what, which channel, when) and asks Claude.
5. The Go bot posts the answer back in the same Slack channel or DM.

## Slack Bot (Go)

- Verifies Slack signatures
- Ingests channel, group, and DM messages
- Answers in DMs, on @mentions, and for `/panda`
- Does not echo every channel message

## Python API (FastAPI)

- SQLite history of Slack messages
- Slack history backfill (`conversations.list` / `conversations.history`)
- `/ask` uses retrieved history as Claude context
