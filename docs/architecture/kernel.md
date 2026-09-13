# Application Kernel

The `Astris` class is the central orchestrator that boots your application, configures the ASGI middleware pipeline, registers database engines, and discovers domain controllers.

## The Application Entrypoint (`main.py`)

In your project's `main.py`:

```python
from astris import Astris

# Initialize and boot the Astris kernel
app = Astris()
```

::: details Step-by-step breakdown

### Step 1: Import `Astris`

```python
from astris import Astris
```

Imports the central application kernel. `Astris` combines high-performance ASGI routing, middleware orchestration, and Inertia response rendering into a cohesive framework instance.

### Step 2: Instantiate `Astris`

```python
app = Astris()
```

Instantiates and boots the application. During this call, the kernel automatically executes the following boot sequence:
1. **Locates the project root**: Determines base paths for `resources/views/root.html`, `public/`, and `app/modules/`.
2. **Loads settings**: Validates `.env` variables against `app/core/config.py`.
3. **Configures middleware**: Installs CORS, static asset handling, encrypted sessions, flash messaging, and CSRF protection.
4. **Discovers modules**: Dynamically imports every `*_controller.py` inside `app/modules/` and mounts its routes.
5. **Sets up database engines**: Prepares the connection pool based on your `DATABASE_URL`.

When you run `uv run orbit serve`, the Uvicorn server points to this `app` variable (`main:app`).

:::

## The Middleware Pipeline

When the kernel initializes, it sets up an enterprise-grade ASGI middleware stack configured in the following order:

```text
Incoming Request
      │
      ▼
┌───────────────────────────────────────┐
│ 1. CORSMiddleware                     │  (Handles preflight OPTIONS requests)
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│ 2. PublicStaticMiddleware             │  (Serves physical files from public/ directly)
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│ 3. SessionMiddleware                  │  (Encrypts & signs session cookies with APP_KEY)
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│ 4. FlashMiddleware                    │  (Persists request.state.flash across redirects)
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│ 5. CSRFMiddleware                     │  (Validates X-XSRF-TOKEN on POST/PUT/DELETE)
└──────────────────┬────────────────────┘
                   │
                   ▼
       Astris Router & Controllers
```

### Middleware Breakdown

1. **`CORSMiddleware`**: Intercepts cross-origin requests, validates allowed origins, methods, and headers, and returns immediate `OPTIONS` preflight responses.
2. **`PublicStaticMiddleware`**: Checks if the requested URL path maps directly to a static file inside `public/` (such as `favicon.ico` or compiled assets in `public/build/`). If a match is found, it streams the file immediately with caching headers.
3. **`SessionMiddleware`**: Reads and decrypts the signed cookie using your `APP_KEY`, making `request.session` accessible across all handlers as a dictionary.
4. **`FlashMiddleware`**: Copies one-time flash messages stored in the session into `request.state.flash` and automatically purges them after the response is sent.
5. **`CSRFMiddleware`**: Issues a readable `XSRF-TOKEN` cookie and verifies the `X-XSRF-TOKEN` header on all mutation requests (`POST`, `PUT`, `PATCH`, `DELETE`).

## Kernel Configuration Options

You can pass custom arguments to `Astris(...)` during instantiation:

```python
from pathlib import Path
from astris import Astris

app = Astris(
    base_path=Path(__file__).parent,
    title="My Custom API",
    enable_csrf=True,
    csrf_exempt_paths=["/api/webhooks/stripe"],
    cors_origins=["https://myapp.com"],
)
```

::: details Parameter breakdown

* **`base_path: Path`**: Explicitly sets the project root directory. Defaults to the directory of the caller script (`Path.cwd()`).
* **`title: str`**: Sets the title displayed in Swagger interactive docs (`/docs`) and ReDoc (`/redoc`).
* **`enable_csrf: bool`**: Enables or disables CSRF verification. Defaults to `True` (or the value of `ENABLE_CSRF` in `.env`).
* **`csrf_exempt_paths: list[str]`**: Defines URL prefixes that should bypass CSRF checks (e.g. external payment webhooks like `/api/webhooks/stripe`).
* **`cors_origins: list[str]`**: Specifies allowed domains for Cross-Origin Resource Sharing. Defaults to `["*"]` in local development.
* **`docs_favicon_url: str | None`**: URL for the custom favicon displayed on Swagger `/docs` and ReDoc `/redoc` pages (defaults to `/favicon.ico`).

:::

::: tip Best Practice: Use `.env` and `Settings`
While constructor parameters are supported for programmatic overrides, configuring your application through your `.env` file and `app/core/config.py` is the recommended best practice.

See [Configuration & .env](/getting-started/configuration) for the full list of available settings.
:::

## Exception Handlers

The kernel automatically configures exception handlers for validation errors and HTTP exceptions:

1. **422 Validation Errors on Inertia Requests**: Automatically transforms validation errors into a `303 See Other` redirect back to the previous page with `$page.props.errors` populated.
2. **Standard API Requests**: Returns structured JSON error payloads with OpenAPI compliance.

## Next Steps

* Write routes and controllers: [Controllers & Routing](/architecture/controllers).
* Learn about HTTP requests and responses: [HTTP Requests & Responses](/architecture/http-requests).
