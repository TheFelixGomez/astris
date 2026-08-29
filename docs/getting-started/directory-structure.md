# Directory Structure

Astris uses an expressive **Domain-Driven Modular Architecture**. Instead of scattering related logic across separate folders (controllers in one directory, models in another), code for a specific feature domain lives together in a dedicated module.

## High-Level Overview

```text
my_app/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Centralized pydantic-settings
│   ├── shared/
│   │   └── __init__.py            # Reusable dependencies, shared utilities
│   └── modules/
│       ├── welcome/               # Default welcome module
│       │   ├── __init__.py
│       │   └── welcome_controller.py
│       └── auth/                  # Default full-stack auth starter module
│           ├── __init__.py
│           ├── auth_controller.py
│           ├── auth_model.py
│           └── auth_service.py
├── database/
│   ├── migrations/                # Alembic schema versions
│   │   ├── versions/
│   │   └── env.py
│   └── app.db                     # SQLite database file (in local dev)
├── public/                        # Static web root (favicon, robots.txt, assets)
│   ├── favicon.ico
│   └── build/                     # Compiled Vite output (in production)
├── resources/
│   ├── css/
│   │   └── app.css                # Tailwind CSS v4 entrypoint
│   ├── js/
│   │   ├── Components/            # Shared Vue 3 components
│   │   │   └── AstrisLogo.vue
│   │   ├── Pages/                 # Inertia.js Vue 3 pages
│   │   │   ├── Welcome.vue
│   │   │   └── Dashboard.vue
│   │   └── app.ts                 # Inertia client bootstrap
│   └── views/
│       └── root.html              # HTML shell containing @inertia & @vite
├── main.py                        # Application entrypoint (Astris kernel)
├── pyproject.toml                 # Python project configuration & dependencies
├── package.json                   # Frontend dependencies (Vue 3, Tailwind, Vite)
└── vite.config.ts                 # Vite + Tailwind plugin configuration
```

## Detailed Directory Breakdown

### `app/core/`
Contains global application configuration. The `config.py` file inherits from `astris.config.Settings` and uses `pydantic-settings` to provide typed environment variables with fail-fast validation on startup.

### `app/modules/`
This is where your application domain logic lives. Each directory represents a business feature (e.g. `billing`, `users`, `products`, `auth`):
* `*_controller.py`: Controller routing and Inertia/JSON responses.
* `*_model.py`: SQLModel database models and Pydantic schemas.
* `*_service.py`: Business logic and database operations.

> **Auto-Discovery**: Any controller defined inside `app/modules/` is automatically discovered and registered by the Astris kernel on startup!

### `database/`
Houses database migrations powered by Alembic. When you run `orbit migrate` or `orbit make:migration`, schema versions are written to `database/migrations/versions/`.

### `public/`
The web root for static files. Any file placed here (such as `favicon.ico`, `robots.txt`, or images) is served directly by Astris at the root URL (e.g. `/favicon.ico`).

### `resources/`
Contains all frontend assets:
* `resources/views/root.html`: The base HTML template loaded on initial page visits. It contains the `@inertia` mount tag and `@vite` script injection.
* `resources/js/Pages/`: Inertia Vue 3 views. When your Python controller returns `InertiaResponse(request, "Dashboard")`, Inertia automatically loads `resources/js/Pages/Dashboard.vue`.
* `resources/js/Components/`: Reusable UI components (buttons, modals, logos, forms).
* `resources/css/app.css`: Tailwind CSS entrypoint (`@import "tailwindcss";`).

## Next Steps

* Configure your environment: [Configuration & Settings](/getting-started/configuration).
* Learn how controllers work: [Controllers & Routing](/architecture/controllers).
