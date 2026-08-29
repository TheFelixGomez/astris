# Controllers & Routing

Astris provides an expressive `Controller` class that wraps FastAPI routing with domain-driven conventions.

::: info Powered by FastAPI
Because Astris is built directly on top of FastAPI, all FastAPI features (including Dependency Injection, parameter validation, background tasks, and OpenAPI schemas) work natively in your controllers.

We highly recommend exploring the [official FastAPI Documentation](https://fastapi.tiangolo.com/) to master advanced routing patterns and unlock the full power of Astris.
:::

## Defining a Controller

To create a controller, instantiate `Controller` inside an `app/modules/<module>/` directory:

```python
from astris.routing import Controller
from astris.http import Request
from astris.inertia import InertiaResponse

# Initialize controller with optional URL prefix and tags
controller = Controller(prefix="/articles", tags=["Articles"])


@controller.get("/")
async def index(request: Request) -> InertiaResponse:
    return InertiaResponse(request, "Articles/Index", props={"articles": []})
```

::: tip Built on FastAPI's `APIRouter`
`Controller` is a direct subclass of FastAPI's `APIRouter`. If you prefer using `APIRouter` from FastAPI directly, it works out of the box with zero changes:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/articles", tags=["Articles"])
```

Astris automatically discovers and registers any `APIRouter` or `Controller` defined inside a `*_controller.py` file in `app/modules/`.
:::

## HTTP Route Decorators

The `Controller` provides decorators for all standard HTTP methods:

```python
@controller.get("/path")
@controller.post("/path")
@controller.put("/path")
@controller.patch("/path")
@controller.delete("/path")
@controller.options("/path")
@controller.head("/path")
```

## Route Parameters

### Path Parameters (`Path`)

URL path parameters can be declared directly as function arguments, or with `Path` for extra validation:

```python
from astris.routing import Controller, Path
from astris.http import Request
from astris.inertia import InertiaResponse

controller = Controller(prefix="/articles")


# 1. Simple type-hinted path parameter
@controller.get("/{article_id}")
async def show(request: Request, article_id: int) -> InertiaResponse:
    return InertiaResponse(request, "Articles/Show", props={"id": article_id})


# 2. With validation and metadata
@controller.get("/by-slug/{slug}")
async def show_by_slug(
    request: Request,
    slug: str = Path(..., min_length=3, description="Article URL slug"),
) -> InertiaResponse:
    return InertiaResponse(request, "Articles/Show", props={"slug": slug})
```

### Query Parameters (`Query`)
```python
from astris.routing import Controller, Query

@controller.get("/")
async def list_items(
    page: int = Query(default=1, ge=1),
    search: str | None = Query(default=None),
):
    return {"page": page, "search": search}
```

### Request Body (`Body`)
```python
from astris.routing import Controller, Body
from pydantic import BaseModel

class CreateArticleDTO(BaseModel):
    title: str
    content: str

@controller.post("/")
async def store(dto: CreateArticleDTO = Body(...)):
    return {"status": "created", "title": dto.title}
```

## Scaffolding a Controller with Orbit

Generate a new controller instantly with the Orbit CLI:

```bash
uv run orbit make:controller billing
```

This creates `app/modules/billing/billing_controller.py` automatically.

## Next Steps

* Master HTTP primitives: [HTTP Requests & Responses](/architecture/http-requests).
* Understand how modules are auto-registered: [Module Auto-Discovery](/architecture/module-discovery).
