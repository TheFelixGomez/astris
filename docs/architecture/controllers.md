# Controllers & Routing

Astris provides an expressive `Controller` class for organizing your application routes with domain-driven conventions.

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

::: details Step-by-step breakdown

### Step 1: Import dependencies

```python
from astris.routing import Controller
from astris.http import Request
from astris.inertia import InertiaResponse
```

* `Controller`: The router class for defining your application routes, handlers, and middleware.
* `Request`: The ASGI request instance containing headers, cookies, session, and client information.
* `InertiaResponse`: The response class that renders an Inertia.js Vue 3 single-page view.

### Step 2: Instantiate `Controller`

```python
controller = Controller(prefix="/articles", tags=["Articles"])
```

* `prefix="/articles"` mounts every route defined on this controller under the `/articles` URL path.
* `tags=["Articles"]` groups all routes in this controller under the "Articles" section in OpenAPI docs (`/docs` and `/redoc`).

### Step 3: Define a route decorator

```python
@controller.get("/")
```

A path operation decorator that tells Astris to handle HTTP `GET` requests directed to `/articles/`.

### Step 4: Define the route handler function

```python
async def index(request: Request) -> InertiaResponse:
```

Defines an asynchronous handler function. Accepting `request: Request` gives you access to the session, headers, and request state.

### Step 5: Return an `InertiaResponse`

```python
    return InertiaResponse(request, "Articles/Index", props={"articles": []})
```

* `request`: Passed as the first parameter so Inertia can attach shared session props and flash messages.
* `"Articles/Index"`: The component name, which Inertia maps directly to `resources/js/Pages/Articles/Index.vue`.
* `props={"articles": []}`: Reactive data passed to the Vue 3 component's `defineProps()`.

:::

::: tip Full `APIRouter` Compatibility
`Controller` is fully compatible with FastAPI's `APIRouter`. If you are migrating existing code or prefer using `APIRouter` directly, Astris automatically discovers and mounts it out of the box:

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

URL path parameters can be declared directly as function arguments, or with `Path` for validation:

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

::: details Breakdown of Path Parameters

* **`{article_id}` in URL pattern**: Tells the router to capture the value from the URL path.
* **`article_id: int` in function signature**: Astris automatically parses the string from the URL into a Python `int`. If a user visits `/articles/abc`, Astris immediately returns an automated `422 Unprocessable Entity` validation error without executing your function.
* **`Path(..., min_length=3)`**: Applies schema constraints. `...` (an ellipsis) marks the parameter as strictly required. `min_length=3` ensures strings shorter than 3 characters are rejected automatically.

:::

### Query Parameters (`Query`)

Declare query parameters using function arguments with default values, or wrap them with `Query` for explicit validation:

```python
from astris.routing import Controller, Query

controller = Controller(prefix="/items")


@controller.get("/")
async def list_items(
    page: int = Query(default=1, ge=1, description="Page number"),
    search: str | None = Query(default=None, max_length=50),
):
    return {"page": page, "search": search}
```

::: details Breakdown of Query Parameters

* **`page: int = Query(default=1, ge=1)`**:
  * If a client calls `/items`, `page` defaults to `1`.
  * If a client calls `/items?page=3`, `page` is parsed as integer `3`.
  * `ge=1` enforces that `page` must be greater than or equal to 1.
* **`search: str | None = Query(default=None, max_length=50)`**:
  * Marks the search query as optional (`None` when not provided).
  * Enforces a maximum length of 50 characters to prevent query abuse.

:::

### Request Body (`Body` & Pydantic Schemas)

When receiving JSON payloads on `POST`, `PUT`, or `PATCH` requests, declare a Pydantic model:

```python
from astris.routing import Controller
from pydantic import BaseModel, Field

controller = Controller(prefix="/articles")


class ArticleCreate(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    content: str = Field(min_length=10)


@controller.post("/")
async def store(dto: ArticleCreate):
    return {"status": "created", "title": dto.title}
```

::: details Breakdown of Request Body Validation

* **`class ArticleCreate(BaseModel)`**: Defines the expected shape, data types, and validation rules of the incoming JSON body.
* **`dto: ArticleCreate`**: Astris reads the HTTP request body, parses the JSON, validates it against `ArticleCreate`, and passes the strongly typed object as `dto`.
* **Automatic Error Handling**: If the request body is missing a field or fails validation, Astris returns a detailed 422 error payload specifying the exact field that failed.

:::

## Inspecting Registered Routes (`has_route`)

Astris provides a helper function `has_route` to verify whether a specific URL route path is currently registered in your application. This is especially useful for conditionally rendering navigation items (such as authentication buttons) or applying dynamic logic:

```python
from astris.http import Request
from astris.inertia import InertiaResponse
from astris.routing import Controller, has_route

controller = Controller()


@controller.get("/")
async def welcome(request: Request) -> InertiaResponse:
    # Check if authentication routes are available
    has_auth = has_route(request, "/login")

    return InertiaResponse(
        request,
        "Welcome",
        props={"has_auth": has_auth},
    )
```

::: details How `has_route` works

* **Accepts either `Request` or `Astris` app instance**: You can pass the current incoming `request` or the application kernel `app`.
* **Recursive traversal**: `has_route` automatically traverses all top-level routes as well as nested sub-routers mounted through domain modules.
* **Exact path matching**: Returns `True` if a registered route matches the target path, or `False` otherwise.

:::

## Scaffolding a Controller with Orbit

Generate a new controller instantly with the Orbit CLI:

```bash
uv run orbit make:controller billing
```

This creates `app/modules/billing/billing_controller.py` automatically.

## Next Steps

* Master HTTP primitives: [HTTP Requests & Responses](/architecture/http-requests).
* Understand how modules are auto-registered: [Module Auto-Discovery](/architecture/module-discovery).
