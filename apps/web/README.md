# Web Frontend

TypeScript/React landing page and settings dashboard for PandaAgent.

## Features

- Landing/settings page
- API health check
- Test message interface
- Responsive design

## Setup

```bash
cd apps/web
npm install
```

## Running Locally

```bash
npm run dev
```

The frontend will be available at `http://localhost:3001`

## Building

```bash
npm run build
npm run preview
```

## Configuration

Environment variables (via `.env`):
- `VITE_API_URL` - Python API URL (default: http://localhost:8000)
