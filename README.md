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

## Deploy to an IPv6-only AWS Lightsail instance

Production uses `docker-compose.production.yml`: PostgreSQL is available only to the
backend container, Gunicorn serves Django, and a host-installed Caddy service serves
as the public HTTPS reverse proxy. The React container and Django container listen
only on `127.0.0.1`, so they are never exposed directly to the internet.

1. Create an Amazon Linux 2023 IPv6-only instance. In the *IPv6* firewall, allow TCP
   ports 22, 80, and 443. Ensure your own connection and your intended users can
   reach IPv6-only sites.
2. Point the production domain's DNS `AAAA` record to the instance's public IPv6
   address before starting Caddy. An IPv6 address survives a restart, but Lightsail
   does not provide a transferable static IPv6 address; update the record if you
   replace the instance or disable/re-enable IPv6.
3. Install Docker Engine, the Docker Compose plugin, and Caddy on the instance, then
   clone this repository there. Install Caddy as a systemd service.
4. Update the committed dependency lock after pulling these changes (this requires
   Docker access and internet access to PyPI):

   ```bash
   docker compose run --rm --no-deps backend poetry lock
   ```

5. Create the production environment file and set real values. `DJANGO_SECRET_KEY`
   and `DB_PASSWORD` must be long random secrets; URL-encode the password in
   `DATABASE_URL` if it contains reserved URL characters.

   ```bash
   cp .env.production.example .env.production
   chmod 600 .env.production
   ```

6. Install the Caddy configuration and provide its domain environment variable:

   ```bash
   sudo install -m 644 deploy/Caddyfile /etc/caddy/Caddyfile
   echo "DOMAIN=your-domain.example" | sudo tee /etc/caddy/.env
   sudo systemctl edit caddy
   ```

   In the systemd editor, add the following and then enable/restart Caddy:

   ```ini
   [Service]
   EnvironmentFile=/etc/caddy/.env
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now caddy
   ```

7. Build and start the private application services:

   ```bash
   docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
   ```

8. Confirm the public health check and inspect startup logs:

   ```bash
   curl -fsS https://your-domain.example/healthz
   docker compose --env-file .env.production -f docker-compose.production.yml logs -f
   ```

The 512 MB bundle can run this low-traffic configuration, but it leaves little memory
headroom for Docker image builds, PostgreSQL, and application traffic. Configure at
least 1 GB of swap before the first build and monitor memory use; move to the 1 GB
bundle if the instance swaps regularly or is OOM-killed. The production Gunicorn and
PostgreSQL settings are intentionally conservative for this size.

The database is kept in the `postgres_data` Docker volume. Take regular Lightsail
snapshots and logical PostgreSQL backups before upgrades. Never expose PostgreSQL
port 5432 publicly or commit `.env.production`.

For deployment updates, pull the desired revision and repeat the `up --build -d`
command. Run this command from the instance so its `.env.production` values are used.

## Project structure

```text
backend/       Django project, gift-list models, migrations, and JSON API
frontend/      React + TypeScript application
docker-compose.yml
```
