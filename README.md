# GoGoGiftList

> Organized gifting for the people who make celebrations happen.

GoGoGiftList is a web app for planning a gift list with family and friends. A list owner creates a list for a gift receiver, adds ideas from a URL or a text note, and assigns each gift to a different giver. Every giver receives a focused, ready-to-shop list—without the duplicate gifts or group-message confusion.

Built for [OpenAI Build Week](https://openai.devpost.com/) · [Devpost project](https://devpost.com/software/gogogiftlist-com)

## The workflow

1. Create an account and start a list for a receiver and occasion.
2. Add gift ideas as a link, a text entry, or both.
3. Add the people who will give gifts and assign each idea to one of them.
4. Copy or email each giver's personalized text list.
5. A giver can create an account using their invitation email to see their assigned gifts in the giver portal.

## Features

- Session-based signup, sign-in, and sign-out
- Multiple gift lists per user and receiver
- URL and text-based gift entries
- Gift-giver management and one-giver-per-gift assignment
- Clipboard-ready and email-ready per-giver shopping lists
- A giver portal for account-linked assignments
- Django-backed persistence with PostgreSQL in Docker Compose (SQLite fallback outside Docker)

## Tech stack

- React and TypeScript with Vite
- Django 6 and Django's built-in authentication
- PostgreSQL in Docker Compose, with SQLite as the default outside Docker
- Bun and Poetry
- Docker Compose

## Run locally

Copy the environment variables required by `docker-compose.yml`, then build and start the application. The backend applies pending database migrations automatically during startup:

```bash
docker compose up --build
```

Open the app at [http://localhost:3000](http://localhost:3000). The Django API is available at [http://localhost:8000](http://localhost:8000).

To stop the web services after testing:

```bash
docker compose stop backend frontend
```

## Development checks

```bash
docker compose run --rm --no-deps backend poetry run python manage.py test gifts
docker compose run --rm --no-deps frontend bun run build
```

## Project structure

```text
backend/       Django project, gift-list models, migrations, and JSON API
frontend/      React + TypeScript application
docker-compose.yml
```
