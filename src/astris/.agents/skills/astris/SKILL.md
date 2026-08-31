---
name: astris
description: Astris best practices and conventions. Use when working with Astris full-stack Python applications, controllers, Inertia.js Vue 3 views, SQLModel databases, Orbit CLI, and security. Keeps Astris code clean and up to date with the latest features and patterns.
---

# Astris

Official Astris skill to write code with best practices, keeping up to date with new versions and features.

## Quick Reference

* Application entrypoint: `app = Astris()` in `main.py`; see [Application Kernel](#application-kernel).
* Configuration: manage via `.env` and `app/core/config.py`; see [Configuration](#configuration-appcoreconfigpy).
* Controllers: define in `app/modules/<name>/<name>_controller.py` with `Controller`; see [Controllers & Routing](#controllers--routing).
* Views: return `InertiaResponse(request, "Component/Path", props={...})`; see [Inertia.js Monolith](#inertiajs-monolith-vue-3--tailwind-css-v4).
* Mutations: return `RedirectResponse(url="/...", status_code=status.HTTP_303_SEE_OTHER)` for POST/PUT/PATCH/DELETE; see [Form Handling & Mutations](#form-handling--mutations).
* Database sessions: inject `DatabaseSession` into services via `Depends()`; see [Database & Services](#database--services).
* Models: define in `app/modules/<name>/<name>_model.py` with `SQLModel`; see [SQLModel Models](#sqlmodel-models).
* Flash messages: use `flash(request, "type", "message")`; see [Flash Messages & Shared Data](#flash-messages--shared-data).
* Authentication: use `auth_required` / `guest_required` route dependencies and `AuthUser`; see [Authentication & Security](#authentication--security).
* Orbit CLI: use `uv run orbit <command>`; see [Orbit CLI](#orbit-cli).

## Application Kernel

Instantiate `Astris()` in `main.py`:

```python
from astris import Astris

app = Astris()
```

The kernel automatically:
1. Loads settings from `app/core/config.py` and `.env`.
2. Registers security middlewares (CORS, PublicStatic, Session, Flash, CSRF).
3. Auto-discovers and attaches all controllers in `app/modules/`.
4. Binds the Inertia.js view engine to `resources/views/root.html`.

## Configuration (`app/core/config.py`)

Astris generates `app/core/config.py` extending the base `Settings` class with automatic `.env` type-casting:

```python
from astris.config import Settings as BaseAppSettings


class Settings(BaseAppSettings):
    """Extend application settings with custom environment variables."""

    stripe_api_key: str | None = None
    redis_url: str = "redis://localhost:6379"


settings = Settings()
```

Access strongly typed settings anywhere in your app:

```python
from app.core.config import settings

api_key = settings.stripe_api_key
db_url = settings.database_url
```

## Controllers & Routing

Place controllers inside `app/modules/<module>/<module>_controller.py`. Astris automatically discovers any `Controller` in files matching `*_controller.py`. `Controller` is a direct subclass of FastAPI's `APIRouter`.

```python
from astris.routing import Controller, Depends, Path, Query
from astris.http import Request
from astris.inertia import InertiaResponse
from app.modules.billing.billing_service import BillingService

controller = Controller(prefix="/billing", tags=["Billing"])


@controller.get("/")
async def index(
    request: Request,
    billing: BillingService = Depends(),
) -> InertiaResponse:
    invoices = billing.get_recent_invoices()
    return InertiaResponse(
        request,
        "Billing/Index",
        props={"invoices": [inv.model_dump() for inv in invoices]},
    )


@controller.get("/{invoice_id}")
async def show(
    request: Request,
    invoice_id: int,
    billing: BillingService = Depends(),
) -> InertiaResponse:
    invoice = billing.get_invoice(invoice_id)
    return InertiaResponse(
        request,
        "Billing/Show",
        props={"invoice": invoice.model_dump()},
    )
```

## Form Handling & Mutations

Inertia requires that mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) redirect with a `303 See Other` status code.

```python
from astris.routing import Controller, Depends
from astris.http import Request, RedirectResponse, status
from astris.inertia import flash
from app.modules.billing.billing_service import BillingService
from app.modules.billing.billing_model import InvoiceCreate

controller = Controller(prefix="/billing", tags=["Billing"])


@controller.post("/")
async def store(
    request: Request,
    dto: InvoiceCreate,
    billing: BillingService = Depends(),
) -> RedirectResponse:
    invoice = billing.create_invoice(dto)
    flash(request, "success", f"Invoice #{invoice.id} created successfully!")
    return RedirectResponse(url="/billing", status_code=status.HTTP_303_SEE_OTHER)


@controller.delete("/{invoice_id}")
async def destroy(
    request: Request,
    invoice_id: int,
    billing: BillingService = Depends(),
) -> RedirectResponse:
    billing.delete_invoice(invoice_id)
    flash(request, "success", "Invoice deleted successfully.")
    return RedirectResponse(url="/billing", status_code=status.HTTP_303_SEE_OTHER)
```

## Flash Messages & Shared Data

* Flash messages set with `flash(request, "success", "...")` are automatically shared with the frontend in `$page.props.flash`.
* Global props can be shared per-request using `share(request, "key", value)`.

```python
from astris.inertia import flash, share

flash(request, "error", "Invalid payment credentials.")
share(request, "team_name", "Acme Corp")
```

## Database & Services

### 1. Service Layer with Injected Session
Accept `session: DatabaseSession` in the constructor:

```python
from astris.database import DatabaseSession, select
from app.modules.billing.billing_model import Invoice, InvoiceCreate


class BillingService:
    def __init__(self, session: DatabaseSession):
        self.session = session

    def get_recent_invoices(self) -> list[Invoice]:
        return self.session.exec(select(Invoice).order_by(Invoice.id.desc())).all()

    def get_invoice(self, invoice_id: int) -> Invoice:
        return self.session.get(Invoice, invoice_id)

    def create_invoice(self, dto: InvoiceCreate) -> Invoice:
        invoice = Invoice.model_validate(dto)
        self.session.add(invoice)
        self.session.commit()
        self.session.refresh(invoice)
        return invoice

    def delete_invoice(self, invoice_id: int) -> None:
        invoice = self.get_invoice(invoice_id)
        if invoice:
            self.session.delete(invoice)
            self.session.commit()
```

### 2. Standalone Scripts & Background Tasks
Use `with db.session() as session:` only outside HTTP requests (in seeders, CLI scripts, or background workers):

```python
from astris.database import db, select
from app.modules.billing.billing_model import Invoice

with db.session() as session:
    invoices = session.exec(select(Invoice)).all()
```

## SQLModel Models

Define models in `app/modules/<module>/<module>_model.py`. Astris auto-imports models to register table metadata with Alembic:

```python
from astris.database import Field, SQLModel


class InvoiceBase(SQLModel):
    customer_name: str = Field(index=True)
    amount: float
    status: str = Field(default="pending")


class Invoice(InvoiceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class InvoiceCreate(InvoiceBase):
    pass


class InvoicePublic(InvoiceBase):
    id: int
```

## Inertia.js Monolith (Vue 3 + Tailwind CSS v4)

Place page components in `resources/js/Pages/<Module>/<Page>.vue`. Always use `<script setup lang="ts">`:

```vue
<script setup lang="ts">
import { useForm, Head, Link, usePage } from '@inertiajs/vue3'

interface Invoice {
  id: number
  customer_name: string
  amount: number
  status: string
}

defineProps<{
  invoices: Invoice[]
}>()

const page = usePage()

const form = useForm({
  customer_name: '',
  amount: 0,
})

const submit = () => {
  form.post('/billing', {
    onSuccess: () => form.reset(),
  })
}
</script>

<template>
  <Head title="Billing" />
  <div class="max-w-4xl mx-auto p-6 space-y-6">
    <!-- Flash Banner -->
    <div
      v-if="page.props.flash?.success"
      class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm"
    >
      {{ page.props.flash.success }}
    </div>

    <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Invoices</h1>

    <!-- Form with Automatic Server Validation Error Bindings -->
    <form @submit.prevent="submit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium">Customer Name</label>
        <input
          v-model="form.customer_name"
          type="text"
          class="w-full px-3 py-2 border rounded-lg"
          :class="{ 'border-rose-500': form.errors.customer_name }"
        />
        <p v-if="form.errors.customer_name" class="text-sm text-rose-500 mt-1">
          {{ form.errors.customer_name }}
        </p>
      </div>

      <button
        type="submit"
        :disabled="form.processing"
        class="px-4 py-2 bg-sky-500 text-white rounded-lg disabled:opacity-50"
      >
        Create Invoice
      </button>
    </form>
  </div>
</template>
```

## Authentication & Security

1. **Guards on Controllers**:
   ```python
   from astris.routing import Controller
   from astris.auth import auth_required, guest_required, AuthUser
   from astris.http import Request
   from astris.inertia import InertiaResponse

   controller = Controller(prefix="/dashboard", dependencies=[auth_required])

   @controller.get("/")
   async def dashboard(request: Request, user: AuthUser) -> InertiaResponse:
       return InertiaResponse(request, "Dashboard", props={"user": user})
   ```

2. **Session Authentication Helpers**:
   * `login_user(request, user_id)`: Log a user in by storing signed session cookie.
   * `logout_user(request)`: Terminate current session.
   * `hash_password(password)` / `verify_password(plain, hashed)`: Secure Argon2id password management.

3. **CSRF Protection**:
   Astris sets the `XSRF-TOKEN` cookie automatically. Inertia and Axios send the `X-XSRF-TOKEN` header on all mutating requests with zero frontend configuration.

## Orbit CLI

Always run Orbit commands via `uv run orbit`:

* `uv run orbit serve`: Start local development server (Uvicorn backend + Vite frontend HMR concurrently).
* `uv run orbit serve --prod`: Start production server on `0.0.0.0` with multi-worker processes.
* `uv run orbit make:module <name>`: Scaffold domain module (`controller`, `service`, `model`).
* `uv run orbit make:controller <name> [--module <mod>]`: Generate a controller.
* `uv run orbit make:model <name> [--module <mod>]`: Generate a SQLModel database table.
* `uv run orbit make:migration "<message>"`: Autogenerate Alembic schema migration from models.
* `uv run orbit migrate`: Execute pending migrations.
* `uv run orbit migrate:rollback`: Roll back database migrations.
* `uv run orbit migrate:status`: Check current migration revisions.
* `uv run orbit key:generate`: Generate a 32-byte secret key and update `APP_KEY` in `.env`.

## Key Rules

* Always configure via `.env` and `app/core/config.py`.
* Never hardcode secrets in code.
* Always use `DatabaseSession` with `Depends()` in route handlers and services.
* Always redirect with `status.HTTP_303_SEE_OTHER` after POST/PUT/PATCH/DELETE mutations.