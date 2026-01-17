# CommandLayer Frontend Console

Minimal Next.js console for executing allowlisted CommandLayer actions and reviewing recent activity.

## Setup

```bash
cd frontend
cp .env.example .env.local
npm install
```

## Run locally

```bash
npm run dev
```

Open `http://localhost:3000`.

## Docker

From repo root:

```bash
docker compose up -d --build
```

Open `http://localhost:3000` for the console and `http://localhost:8000/docs` for API docs.

## Screenshots

Add screenshots to the PR when available:

- `docs/screenshots/console.png`
- `docs/screenshots/log-details.png`
