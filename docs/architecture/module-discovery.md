# Module Auto-Discovery

Astris eliminates the need to manually import and attach routers in your `main.py`.

## How It Works

During application boot, the `Astris` kernel automatically scans the `app/modules/` directory recursively:

```text
app/modules/
├── welcome/
│   └── welcome_controller.py      <-- Auto-discovered
├── auth/
│   └── auth_controller.py         <-- Auto-discovered
└── billing/
    └── billing_controller.py      <-- Auto-discovered
```

1. It dynamically imports each module.
2. It inspects module attributes for instances of `astris.routing.Controller` (or `fastapi.APIRouter`).
3. It automatically registers the discovered router on the Astris application.

## Example Domain Module

```text
app/modules/billing/
├── __init__.py
├── billing_model.py       # SQLModel database schemas
├── billing_service.py     # Domain business logic
└── billing_controller.py  # HTTP routes & Inertia responses
```

### 1. `billing_model.py` (Database Model)
Defines SQLModel database tables. Astris automatically imports model files on startup to register table metadata:

```python
from astris.database import SQLModel, Field


class Invoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    customer_id: int
    amount: float
    status: str = Field(default="pending")
```

### 2. `billing_service.py` (Business Logic)
Encapsulates database operations and business logic with an injected database session:

```python
from astris.database import DatabaseSession, select
from app.modules.billing.billing_model import Invoice


class BillingService:
    def __init__(self, session: DatabaseSession):
        self.session = session

    def get_recent_invoices(self) -> list[Invoice]:
        return self.session.exec(select(Invoice).order_by(Invoice.id.desc())).all()
```

### 3. `billing_controller.py` (Routes & Responses)
Astris automatically resolves `BillingService` and its session dependencies when injected with `Depends()`:

```python
from astris.routing import Controller, Depends
from astris.http import Request
from astris.inertia import InertiaResponse
from app.modules.billing.billing_service import BillingService

controller = Controller(prefix="/billing", tags=["Billing"])


@controller.get("/")
async def billing_home(
    request: Request,
    billing: BillingService = Depends(),
) -> InertiaResponse:
    invoices = billing.get_recent_invoices()
    return InertiaResponse(
        request,
        "Billing/Index",
        props={"invoices": [inv.model_dump() for inv in invoices]},
    )
```

**That's it!** Simply placing your domain module in `app/modules/billing/` registers the database models and makes `/billing` active across your application.

## Scaffolding Modules with Orbit

To scaffold an entire domain module (controller, model, view) with one command:

```bash
uv run orbit make:module billing
```

## Next Steps

* Connect Vue 3 and Python: [Inertia.js Overview](/frontend/inertia).
* Render frontend pages: [Rendering Responses](/frontend/responses).
