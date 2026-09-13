# Rendering Responses

To render an Inertia view from Python, return an `InertiaResponse`.

## Basic Usage

```python
from astris.routing import Controller
from astris.http import Request
from astris.inertia import InertiaResponse

controller = Controller(prefix="/dashboard")


@controller.get("/")
async def dashboard(request: Request) -> InertiaResponse:
    return InertiaResponse(
        request=request,
        component="Dashboard",
        props={
            "user_name": "Jane Doe",
            "stats": {"total_sales": 1540, "active_users": 89},
        },
    )
```

::: details Step-by-step breakdown

### Step 1: Import dependencies

```python
from astris.routing import Controller
from astris.http import Request
from astris.inertia import InertiaResponse
```

* `Controller`: Organizes route endpoints for your module.
* `Request`: Provides access to session state, headers, and protocol metadata.
* `InertiaResponse`: Renders an Inertia page view.

### Step 2: Return an `InertiaResponse`

```python
return InertiaResponse(
    request=request,
    component="Dashboard",
    props={
        "user_name": "Jane Doe",
        "stats": {"total_sales": 1540, "active_users": 89},
    },
)
```

* **`request=request`**: Crucial for Inertia protocol negotiation. The kernel inspects the incoming `X-Inertia` header. If present, it returns an Inertia JSON payload. If absent (e.g. initial browser page load), it renders the full HTML shell (`root.html`).
* **`component="Dashboard"`**: The component name, resolved relative to `resources/js/Pages/`. This loads `resources/js/Pages/Dashboard.vue`.
* **`props={...}`**: Dictionary of serializable data delivered to the Vue 3 component. Any Python dictionaries, lists, strings, numbers, or Pydantic/SQLModel models are automatically serialized.

:::

### Component Resolution Conventions
* `"Dashboard"` resolves to `resources/js/Pages/Dashboard.vue`.
* `"Articles/Index"` resolves to `resources/js/Pages/Articles/Index.vue`.
* `"Settings/Billing/Invoices"` resolves to `resources/js/Pages/Settings/Billing/Invoices.vue`.

## Receiving Props in Vue 3

Inside your Vue 3 Single File Component (SFC), define and type your props using TypeScript and `<script setup>`:

```vue
<script setup lang="ts">
interface Props {
  user_name: string;
  stats: {
    total_sales: number;
    active_users: number;
  };
}

const props = defineProps<Props>();
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold">Welcome, {{ props.user_name }}</h1>
    <p>Total Sales: {{ props.stats.total_sales }}</p>
  </div>
</template>
```

::: details Component breakdown

* **`<script setup lang="ts">`**: The modern Vue 3 composition API syntax with TypeScript support.
* **`interface Props { ... }`**: Defines compile-time type checking for the exact props passed from your Python controller.
* **`const props = defineProps<Props>()`**: Registers the props with Vue's reactivity system. They are immediately available both in your `<script>` and `<template>`.

:::

## The Root HTML Template (`resources/views/root.html`)

On the initial visit (hard reload or direct URL navigation in the browser address bar), Astris renders `resources/views/root.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <title>Astris Application</title>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans">
    @inertia

    @vite
</body>
</html>
```

::: details Template directives breakdown

* **`@inertia`**: Replaced by Astris with the root HTML mounting point:
  ```html
  <div id="app" data-page='{"component":"Dashboard","props":{...},"url":"/dashboard"}'></div>
  ```
* **`@vite`**: Injects Vite HMR client scripts in development (`http://localhost:5173/@vite/client` and `/resources/js/app.ts`), and preloaded production bundles with CSS stylesheets when built for production.

:::

## Next Steps

* Share data across all pages: [Shared Props & Flash Data](/frontend/shared-data).
* Handle forms and validations: [Forms & Validation](/frontend/forms-validation).
