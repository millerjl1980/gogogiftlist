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

## Deploy to a dual-stack Ubuntu AWS Lightsail instance

Production uses `docker-compose.production.yml`: PostgreSQL is available only to the
backend container, Gunicorn serves Django, and a host-installed Caddy service serves
as the public HTTPS reverse proxy. The React container and Django container listen
only on `127.0.0.1`, so they are never exposed directly to the internet.

1. Create an Ubuntu 22.04 dual-stack instance and attach a Lightsail static IPv4
   address. In both the *IPv4* and *IPv6* firewalls, allow TCP ports 22, 80, and 443.
2. Point the production domain's DNS `A` record to the static IPv4 address and its
   `AAAA` record to the public IPv6 address before starting Caddy. The IPv6 address
   survives a restart but is not transferable; update the `AAAA` record if you replace
   the instance or disable/re-enable IPv6.
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

## Automatic deployments from GitHub

The repository includes [`.github/workflows/deploy-lightsail.yml`](.github/workflows/deploy-lightsail.yml),
which deploys every push to `main` (and can also be run manually). The workflow uses
SSH and `rsync`; it does not give the Lightsail server access to GitHub. It preserves
the server's `.env.production` and PostgreSQL Docker volume, uploads the checked-out
revision, then runs the production Compose command and checks `/healthz`.

Use the instance's static public IPv4 address for the GitHub Actions SSH connection.
This avoids any GitHub-runner IPv6 reachability dependency; keep the `AAAA` DNS record
so visitors can still use IPv6.

### 1. Prepare the Lightsail instance

Complete the production setup above first, including Docker, Docker Compose, Caddy,
DNS, and a working `.env.production`. Then, as the account that will run deployments:

```bash
sudo apt-get update
sudo apt-get install -y rsync
sudo mkdir -p /srv/gogogiftlist
sudo chown "$USER":"$USER" /srv/gogogiftlist
```

For Ubuntu Lightsail instances, the usual deployment user is `ubuntu`. Confirm that
user can run Docker without `sudo` (the workflow invokes `docker compose` directly):

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker version
```

Copy the repository to `/srv/gogogiftlist` once (or clone it), create
`/srv/gogogiftlist/.env.production` as in step 5 above, and run the initial production
deployment from that directory. This initial copy is necessary because the GitHub
workflow deliberately never transfers production secrets.

Create a dedicated SSH key for GitHub Actions, append its public half to the deploying
user's `~/.ssh/authorized_keys`, and keep the private half only for GitHub:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/gogogiftlist-github-actions -C gogogiftlist-github-actions
cat ~/.ssh/gogogiftlist-github-actions.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Record the server's SSH host key from a trusted connection. Do this from the Lightsail
console or an already verified SSH session—not from an unverified network lookup:

```bash
ssh-keyscan -t ed25519 -p 22 your-static-public-ipv4-address
```

Save the exact line that command prints. Ensure the Lightsail firewall permits SSH
from GitHub Actions (port 22); if you restrict SSH by source IP, use GitHub's published
Actions runner IP ranges and keep them updated. The existing IPv6 firewall rules for
80 and 443 remain required for the app.

### 2. Configure the GitHub repository

In **Settings → Secrets and variables → Actions**, add these repository secrets:

| Secret | Value |
| --- | --- |
| `LIGHTSAIL_SSH_PRIVATE_KEY` | Entire contents of `~/.ssh/gogogiftlist-github-actions` (the private key) |
| `LIGHTSAIL_SSH_KNOWN_HOSTS` | The verified `known_hosts` line recorded above |

Add these repository variables in the same screen:

| Variable | Value |
| --- | --- |
| `LIGHTSAIL_HOST` | The Lightsail static public IPv4 address (or DNS hostname with an `A` record) |
| `LIGHTSAIL_USER` | The Linux user that owns `/srv/gogogiftlist` and can run Docker (normally `ubuntu`) |
| `LIGHTSAIL_SSH_PORT` | `22` (optional; the workflow defaults to this) |
| `LIGHTSAIL_DEPLOY_PATH` | `/srv/gogogiftlist` (optional; this is the workflow default) |

Commit these files and merge or push them to `main`. The Actions tab will show the
first deployment; use **Run workflow** there to deploy manually. A successful run
ends by querying the app's `/healthz` endpoint through the backend container. If a
deployment fails, inspect the workflow log first, then on the instance run:

```bash
cd /srv/gogogiftlist
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=200
```

## Project structure

```text
backend/       Django project, gift-list models, migrations, and JSON API
frontend/      React + TypeScript application
docker-compose.yml
```
