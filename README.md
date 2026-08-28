<p align="center" style="padding: 20px 0 10px 0;">
  <a href="https://github.com/TheFelixGomez/astris">
    <img src="https://raw.githubusercontent.com/TheFelixGomez/astris/main/.github/assets/astris-logo-name.png" alt="Astris" width="380">
  </a>
</p>

<p align="center">
  <strong>The modern full-stack web framework for Python.</strong><br>
  Full-stack simplicity with modern Python performance.
</p>

<p align="center">
  <a href="https://pypi.org/project/astris-python/"><img src="https://img.shields.io/pypi/v/astris-python.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/astris-python/"><img src="https://img.shields.io/pypi/pyversions/astris-python.svg" alt="Python Versions"></a>
  <a href="https://github.com/TheFelixGomez/astris/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

> ⚠️ **Early Alpha**: Astris is currently in active alpha development. APIs and features may undergo breaking changes until production-ready status is confirmed. Feedback, bug reports, and ideas are welcome!

---

## What is Astris?

**Astris** bridges the gap between the rapid, joyful developer experience of classic full-stack frameworks (like Laravel and Rails) and the raw performance, modern typing, and async concurrency of **FastAPI** and **Python 3.11+**.

By combining **FastAPI**, **Inertia.js**, **Vue 3**, **Tailwind CSS v4**, and **SQLModel**, Astris lets you build rich, dynamic single-page applications without the overhead of maintaining separate API layers or complex state synchronization.

---

## 🌟 Key Features

* **⚡ Lightning-Fast Core**: ASGI performance powered by FastAPI and Uvicorn with auto-generated OpenAPI & Swagger documentation.
* **🧩 Modern Monolith with Inertia.js**: Render Vue 3 components directly from FastAPI controllers with full server-side state hydration and zero REST boilerplate.
* **🛡️ Production-Ready Authentication**: Cryptographically signed cookie sessions, OWASP-standard **Argon2id** password hashing (`pwdlib`), and full-stack auth starter kit.
* **🗄️ SQLModel & Alembic Database Engine**: Unified declarative models, DTOs, and automatic schema migrations out-of-the-box.
* **⚙️ Type-Safe Centralized Configuration**: Powered by `pydantic-settings` for `.env` management, type casting, and fail-fast startup validation.
* **🪐 Orbit CLI**: An artisan developer CLI for scaffolding modules, generating migrations, and serving full-stack applications with hot-reloading.
* **🎨 Tailwind CSS v4 Pre-configured**: Instant zero-config styling powered by `@tailwindcss/vite`.

---

## 🚀 Quickstart

Create a new full-stack Astris application in seconds using `uvx` (or `pipx`):

```bash
# 1. Create a new project
uvx --from astris-python astris new my_app

# Or install globally as a CLI tool:
# uv tool install astris-python
# astris new my_app

# 2. Enter directory and install frontend dependencies
cd my_app
npm install

# 3. Start full-stack development server (FastAPI + Vite HMR)
uv run orbit serve
```

Open **`http://localhost:8000`** in your browser. Your full-stack app with authentication, Inertia.js, and SQLite is live!

---

## 💡 How It Feels

### 1. Controllers & Inertia Rendering
Write clean, expressive controllers that return frontend views or JSON seamlessly:

```python
from astris.auth import AuthUser, auth_required
from astris.inertia import InertiaResponse
from astris.routing import Controller

controller = Controller(prefix="/dashboard", dependencies=[auth_required])


@controller.get("/")
async def dashboard_page(request: Request, user: AuthUser) -> InertiaResponse:
    # Props are passed directly to Vue 3 with $page.props
    return InertiaResponse(request, "Dashboard", props={"username": user["name"]})
```

### 2. Unified SQLModel Models
Define database tables and validation schemas in a single declarative model:

```python
from astris.database import Field, SQLModel


class ArticleBase(SQLModel):
    title: str = Field(index=True)
    content: str
    is_published: bool = Field(default=False)


class Article(ArticleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ArticleCreate(ArticleBase):
    pass
```

### 3. Frontend Views (Vue 3 + Inertia)
Build dynamic reactive pages without configuring client-side routers:

```vue
<script setup lang="ts">
import { Head, Link } from '@inertiajs/vue3'

defineProps<{
  username: string
}>()
</script>

<template>
  <Head title="Dashboard" />
  <div class="min-h-screen bg-slate-950 text-slate-100 p-8">
    <h1 class="text-3xl font-bold">Welcome back, {{ username }}!</h1>
  </div>
</template>
```

---

## 🪐 The Orbit CLI

Astris comes equipped with **Orbit**, a developer toolkit for rapid development:

```bash
# Start FastAPI backend + Vite frontend concurrently
uv run orbit serve

# Scaffold a new domain module (controller, service, model)
uv run orbit make:module billing

# Create and apply database migrations
uv run orbit make:migration "create_billing_table"
uv run orbit migrate

# Generate encryption keys
uv run orbit key:generate
```

---

## 📂 Project Architecture

Astris structures projects with a modular, **Domain-Driven Design** that grows gracefully:

```
my_app/
├── app/
│   ├── core/
│   │   └── config.py        # Centralized Pydantic settings & .env loading
│   └── modules/
│       ├── auth/            # Authentication domain (controller, service, model)
│       └── welcome/         # Welcome domain
├── database/
│   └── migrations/          # Alembic database migration versions
├── resources/
│   ├── css/
│   │   └── app.css          # Tailwind CSS v4 styling
│   ├── js/
│   │   ├── Pages/           # Inertia Vue 3 views & components
│   │   └── app.ts           # Vue entrypoint
│   └── views/
│       └── root.html        # HTML shell template
├── .env                     # App configuration & APP_KEY
└── pyproject.toml           # Python dependencies
```

---

## 🙏 Acknowledgments

Astris is built upon the work of giants. Huge gratitude to the incredible open-source projects and creators that make Astris possible:

* **[FastAPI](https://fastapi.tiangolo.com/) & [SQLModel](https://sqlmodel.tiangolo.com/)** by [Tiangolo](https://github.com/tiangolo) - for setting the standard in modern Python type safety, speed, and ergonomics.
* **[Inertia.js](https://inertiajs.com/)** by [Jonathan Reinink](https://github.com/reinink) - for the modern monolith architecture that bridges backend controllers and frontend SPAs without API boilerplate.
* **[Vue.js](https://vuejs.org/)** by [Evan You](https://github.com/yyx990803) - for the approachable and performant frontend component framework.
* **[Starlette](https://www.starlette.io/) & [Uvicorn](https://www.uvicorn.org/)** by [Encode](https://www.encode.io/) - for the lightning-fast ASGI toolkit and web server engine.
* **[Pydantic](https://docs.pydantic.dev/)** by [Samuel Colvin](https://github.com/samuelcolvin) & team - for rock-solid runtime data validation and centralized settings.
* **[Tailwind CSS](https://tailwindcss.com/)** by [Tailwind Labs](https://github.com/tailwindlabs) - for zero-config utility-first styling.
* **[Laravel](https://laravel.com/)** by [Taylor Otwell](https://github.com/taylorotwell) - for inspiring developer-first framework craftsmanship.

---

## 📄 License

The Astris framework is open source and licensed under the terms of the MIT license.

Built with ❤️ by [Felix Gomez](https://github.com/TheFelixGomez).
