# Introduction

**Astris** is the modern full-stack web framework for Python.

It bridges the gap between the rapid, joyful developer experience of classic full-stack frameworks (like Laravel and Rails) and the raw performance, modern typing, and async concurrency of **FastAPI** and **Python 3.11+**.

## Why Astris?

For years, building web applications in Python required choosing between two extremes:

1. **Traditional Server-Side Monoliths** (like Django with template tags): Great developer velocity, but clunky when building rich, dynamic, stateful user interfaces.
2. **Decoupled API + SPA Architectures**: FastAPI backend + separate React/Vue frontend. Highly reactive, but introduces massive boilerplate: dual repositories, OpenAPI client generation, manual state management, CORS debugging, and dual auth tokens.

**Astris eliminates this dilemma.**

By combining **FastAPI**, **Inertia.js**, **Vue 3**, **Tailwind CSS v4**, and **SQLModel**, Astris gives you the single-page application user experience with classic server-side monolithic developer velocity.

## Key Pillars of Astris

### 1. ⚡ ASGI Performance & Async First
Built on top of FastAPI and Starlette, Astris delivers ultra-high throughput ASGI execution with asynchronous request handling and automatic OpenAPI documentation.

### 2. 🧩 The Modern Monolith with Inertia.js
You write standard server-side Python controllers that return frontend components:
```python
@controller.get("/dashboard")
async def dashboard(request: Request, user: AuthUser) -> InertiaResponse:
    return InertiaResponse(request, "Dashboard", props={"username": user["name"]})
```
No REST endpoints to maintain. No GraphQL schemas. No Axios state synchronization. Inertia hydrates your Vue 3 components on the fly.

### 3. 🛡️ Production-Ready Security
* **Argon2id Password Hashing**: State-of-the-art password security powered by `pwdlib`.
* **Cryptographically Signed Cookie Sessions**: Tamper-proof, encrypted browser cookies.
* **Automatic CSRF Protection**: Built-in cookie-to-header token verification with zero configuration.

### 4. 🗄️ Unified Database Layer
Define your database tables, SQL queries, and validation schemas in a single declarative model powered by **SQLModel** and **Alembic**.

### 5. 🪐 The Orbit CLI
An artisan command-line companion that scaffolds domain modules, runs migrations, generates secret keys, and serves your full-stack app with hot-reloading.

## Next Steps

* Ready to build? Jump to [Installation & Quickstart](/getting-started/installation).
* Want to understand project layout? Read [Directory Structure](/getting-started/directory-structure).
