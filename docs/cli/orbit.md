# Orbit CLI Reference

**Orbit** is Astris's artisan command-line companion for developing, scaffolding, and managing your applications.

## Available Commands

| Command | Description |
| :--- | :--- |
| `orbit serve` | Start full-stack development server with concurrent Vite HMR |
| `orbit make:module <name>` | Scaffold a complete domain module (Controller, Service, Model) |
| `orbit make:controller <name>` | Generate an Astris controller |
| `orbit make:model <name>` | Generate a SQLModel database model |
| `orbit make:auth` | Install full-stack authentication starter kit |
| `orbit migrate` | Run all pending database migrations |
| `orbit make:migration "<msg>"` | Auto-generate a new Alembic schema migration |
| `orbit key:generate` | Generate a new 32-byte secret `APP_KEY` in `.env` |

## Command Details

### 1. `orbit serve`
Launches the backend (Uvicorn) and frontend (Vite) development servers concurrently:

```bash
uv run orbit serve
```

* **Backend**: `http://localhost:8000`
* **Vite HMR**: Hot reload for Vue 3 and CSS changes without page reloads.

#### Production Mode (`--prod`)
To run in production mode (binds to `0.0.0.0`, disables reload/Vite, enables multi-worker):

```bash
uv run orbit serve --prod --workers 4
```

### 2. `orbit make:module <name>`
Scaffolds a complete domain module with controller, service, and SQLModel schemas:

```bash
uv run orbit make:module billing
```

Creates:
* `app/modules/billing/__init__.py`
* `app/modules/billing/billing_controller.py`
* `app/modules/billing/billing_service.py`
* `app/modules/billing/billing_model.py`

### 3. `orbit make:controller <name>`
Scaffolds an Astris controller inside a domain module:

```bash
uv run orbit make:controller reports
```

Creates:
* `app/modules/reports/reports_controller.py`

You can also specify a custom target module:
```bash
uv run orbit make:controller payments --module billing
```

### 4. `orbit make:model <name>`
Scaffolds a SQLModel database table and DTO validation schemas:

```bash
uv run orbit make:model Invoice
```

Creates:
* `app/modules/invoice/invoice_model.py`

### 5. `orbit make:auth`
Scaffolds the full-stack authentication starter kit:

```bash
uv run orbit make:auth
```

Creates:
* `app/modules/auth/auth_controller.py`
* `app/modules/auth/auth_service.py`
* `app/modules/auth/auth_model.py`
* `resources/js/Components/AstrisLogo.vue`
* `resources/js/Pages/Auth/Login.vue`
* `resources/js/Pages/Auth/Register.vue`
* `resources/js/Pages/Dashboard.vue`

### 6. `orbit make:migration "<message>"`
Auto-generates a versioned schema migration by comparing your SQLModel models against the current database:

```bash
uv run orbit make:migration "create_articles_table"
```

Creates:
* `database/migrations/versions/<timestamp>_create_articles_table.py`

### 7. `orbit migrate`
Executes all pending database migrations against your configured `DATABASE_URL`:

```bash
uv run orbit migrate
```

To roll back the last migration:
```bash
uv run orbit migrate:rollback
```

To check migration status:
```bash
uv run orbit migrate:status
```

### 8. `orbit key:generate`
Generates a cryptographically secure 32-byte secret key and updates `APP_KEY` in `.env`:

```bash
uv run orbit key:generate
```

To display the generated key in the terminal without writing to `.env` (useful for CI/CD pipelines):
```bash
uv run orbit key:generate --show
```

**When to use this command:**
* After cloning an existing project and copying `.env.example` to `.env`.
* When provisioning a new environment (staging, production).
* When rotating application secrets for security maintenance.
*(Note: `APP_KEY` is already generated automatically when you create a project with `astris new`.)*

## Next Steps

* Project generator CLI: [Astris Project Generator](/cli/astris).
* Deploying to production: [Production & Docker](/deployment/production).
