FROM python:3.12-slim

# Install system dependencies for Postgres and Poetry
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# FIXED: Force Poetry to create the virtual environment inside your /app folder (.venv)
# This allows the virtual environment to persist perfectly across your Docker volume mounts
RUN poetry config virtualenvs.in-project true

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies (creates the local .venv folder inside the container)
RUN poetry install --no-root

# Copy the rest of your application code
COPY . /app/