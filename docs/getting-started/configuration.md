# Configuration & Environment

Astris uses **`pydantic-settings`** for type-safe environment configuration with fail-fast validation on startup.

## The `.env` File

When you create an application, Astris generates a default `.env` and `.env.example`:

```ini
APP_NAME=My_App
APP_ENV=local
APP_DEBUG=true
APP_KEY=random_32_byte_secret_key

DATABASE_URL=sqlite:///database/app.db
```

## Centralized Settings (`app/core/config.py`)

Your project contains an `app/core/config.py` file that extends Astris's base `Settings` class:

```python
from astris.config import Settings as BaseAppSettings


class Settings(BaseAppSettings):
    """Extend application settings with custom environment variables."""

    stripe_api_key: str | None = None
    redis_url: str = "redis://localhost:6379"
    max_upload_size_mb: int = 25


settings = Settings()
```

::: details Step-by-step breakdown

### Step 1: Import `BaseAppSettings`

```python
from astris.config import Settings as BaseAppSettings
```

Imports Astris's base configuration class. It inherits from Pydantic's `BaseSettings` and automatically locates and parses `.env` files in your project root.

### Step 2: Create a `Settings` subclass

```python
class Settings(BaseAppSettings):
    """Extend application settings with custom environment variables."""
```

Creates your application's custom configuration schema. By subclassing `BaseAppSettings`, your settings inherit built-in variables (like `APP_NAME`, `APP_KEY`, and `DATABASE_URL`).

### Step 3: Add typed environment variables

```python
    stripe_api_key: str | None = None
    redis_url: str = "redis://localhost:6379"
    max_upload_size_mb: int = 25
```

* **`stripe_api_key`**: Declares an optional setting. If `STRIPE_API_KEY` is not set in `.env`, it defaults to `None`.
* **`redis_url`**: Declares a required string setting with a sensible default value. If `REDIS_URL` is set in `.env`, that value is used instead.
* **`max_upload_size_mb`**: Enforces automatic type casting. Because environment variables are always strings in the operating system, Pydantic converts strings like `"50"` into an integer `50`. If an invalid value like `"large"` is provided, the application fails fast on startup with a clear error message.

### Step 4: Instantiate the `settings` singleton

```python
settings = Settings()
```

Environment variables are read, validated, and cached once at boot time. You can now import `settings` anywhere in your application.

:::

## Built-In Framework Settings

The following settings are built into Astris and can be customized in `.env` or overridden in `Settings`:

| Setting Key | Default | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"Astris Application"` | Title used in OpenAPI docs and page headers |
| `APP_ENV` | `"local"` | Environment mode (`local`, `staging`, `production`) |
| `APP_DEBUG` | `True` | Enables debug mode and verbose error messages |
| `APP_KEY` | `""` | 32-byte secret key used for cookie encryption and session signing |
| `DATABASE_URL` | `"sqlite:///database/app.db"` | Database connection string (SQLite, PostgreSQL, MySQL) |
| `DB_ECHO` | `False` | Prints raw SQL queries to console when True |
| `AUTO_CREATE_TABLES` | `auto` | Auto-create tables on boot (`True` in local development, `False` when `APP_ENV=production`) |
| `ENABLE_CSRF` | `True` | Enables automatic CSRF protection |
| `SESSION_COOKIE_NAME` | `"astris_session"` | Name of the signed session cookie |
| `SESSION_MAX_AGE` | `1209600` (14 days) | Session expiration time in seconds |
| `SESSION_HTTPS_ONLY` | `auto` | Forces session cookies to HTTPS only (`True` when `APP_ENV=production`, `False` in local development) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins for API requests |

## Generating an `APP_KEY`

To generate or rotate a cryptographically secure 32-byte `APP_KEY` in your `.env` file:

```bash
uv run orbit key:generate
```

::: tip Automatically Generated on Project Creation
When you scaffold a new project with `astris new`, a unique 32-byte `APP_KEY` is automatically generated and written to your `.env` file. You only need to run `orbit key:generate` if you wish to rotate your secret key or configure a fresh environment.
:::

## Accessing Settings in Your Code

To use your settings anywhere in your application (controllers, services, tasks):

```python
from app.core.config import settings

# Access strongly typed values
api_key = settings.stripe_api_key
db_url = settings.database_url
is_debug = settings.app_debug
```

### How to Use It

1. **Import `settings` directly**: Import the instantiated singleton from `app.core.config`.
2. **Access attributes with full autocompletion**: Your IDE provides autocomplete and type-checking for every field defined on your `Settings` model.
3. **Environment precedence**: If a variable is exported in your system shell (e.g., in Docker or CI/CD), it takes precedence over the `.env` file.

## Next Steps

* Understand the application kernel: [Application Kernel](/architecture/kernel).
* Write your first controller: [Controllers & Routing](/architecture/controllers).
