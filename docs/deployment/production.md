# Production & Docker

Deploying an Astris application is simple and standard.

## 1. Building Frontend Assets

Before running in production, compile your Vue 3 and Tailwind CSS assets into optimized bundles:

```bash
npm run build
```

This compiles your frontend code into `public/build/` with a production manifest (`manifest.json`).

## 2. Environment Configuration

In production, set your environment variables:

```ini
APP_ENV=production
APP_DEBUG=false
APP_KEY=your_secure_32_byte_secret_key
SESSION_HTTPS_ONLY=true
DATABASE_URL=postgresql+psycopg://user:password@db_host:5432/production_db
```

## 3. Starting the Production Server (`orbit serve --prod`)

Launch your application in production mode using the Orbit CLI:

```bash
uv run orbit serve --prod
```

This automatically:
* Binds to `0.0.0.0`
* Disables development auto-reload and the Vite dev server
* Enables multi-worker process management (defaults to 4 workers)

You can customize the port or worker count with flags:
```bash
uv run orbit serve --prod --port 8000 --workers 8
```

## 4. Docker Deployment

Here is a recommended multi-stage `Dockerfile` for Astris:

```dockerfile
# Stage 1: Build Frontend Assets
FROM node:24-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Python Runtime
FROM python:3.14-slim
WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency specifications
COPY pyproject.toml .
RUN uv sync --frozen --no-dev

# Copy application source & built frontend assets
COPY . .
COPY --from=frontend-builder /app/public/build ./public/build

EXPOSE 8000
CMD ["uv", "run", "orbit", "serve", "--prod"]
```

## Next Steps

* Visit the GitHub repository: [Astris on GitHub](https://github.com/TheFelixGomez/astris).
* Share feedback and contribute: [Issues & Discussions](https://github.com/TheFelixGomez/astris/issues).
