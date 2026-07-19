# Project Sandbox Instructions

## Environment
You are operating entirely within an isolated Dockerized development environment.
- **Backend:** Django (Python 3.12) managed via Poetry.
- **Frontend:** React managed via Bun.
- **Database:** PostgreSQL 15.

## Execution Rules
1. **Isolation:** Do NOT attempt to execute bare terminal commands on the host machine. You do not have permission to use the host's global environment.
2. **Backend Commands:** All backend-related tasks must be proxied through the `backend` container using non-interactive shells.
   - Core runtime hook: `docker compose exec backend poetry run <command>`
3. **Frontend Commands:** All frontend build and package operations must execute within the `frontend` service.
   - Core runtime hook: `docker compose exec frontend bun <command>`
4. **File Access:** You have full read/write access to the `/app` directory inside the containers, which is mapped via volume hooks directly to the project root on the host machine.

## Common Development Workflow Hooks
When writing code or adding functionality, use these exact command templates:

### 🐍 Backend (Django & Poetry)
- Add a package: `docker compose exec backend poetry add <package>`
- Create a migration: `docker compose exec backend poetry run python manage.py makemigrations`
- Run migrations: `docker compose exec backend poetry run python manage.py migrate`
- Execute tests: `docker compose exec backend poetry run python manage.py test`

### ⚡ Frontend (React & Bun)
- Add a package: `docker compose exec frontend bun add <package>`
- Run dev mode locally: `docker compose exec frontend bun run dev --host 0.0.0.0 --port 3000`
- Run frontend tests: `docker compose exec frontend bun test`

## Setup Verification
Confirm your environment parameters by checking that the local `backend/pyproject.toml` lists `python = "^3.12"` before running initial workspace scaffolding.