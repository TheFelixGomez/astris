# Application Kernel

The `Astris` class is the central orchestrator that boots your application, configures the ASGI middleware pipeline, registers database engines, and discovers domain controllers.

## The Application Entrypoint (`main.py`)

In your project's `main.py`:

```python
from astris import Astris

# Initialize and boot the Astris kernel
app = Astris()
```

The `app` instance created by `Astris()` automatically loads settings from your environment, initializes database connections, configures middleware, and auto-discovers your domain controllers. When you run `uv run orbit serve`, Astris serves this application directly with full-stack hot-reloading.

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
       FastAPI Router & Controllers
```

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
