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

Inertia maps `"Dashboard"` to the file located at:
`resources/js/Pages/Dashboard.vue`

Nested components like `"Articles/Edit"` map to:
`resources/js/Pages/Articles/Edit.vue`

## Receiving Props in Vue 3

Inside your Vue 3 SFC component, define your props using TypeScript:

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

## The Root HTML Template (`resources/views/root.html`)

On the initial visit (hard reload / direct URL entry), Astris renders `resources/views/root.html`:

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

* `@inertia`: Mounts the `<div id="app" data-page="..."></div>` element.
* `@vite`: Injects the Vite client and compiled bundle scripts (`resources/js/app.ts`).

## Next Steps

* Share data across all pages: [Shared Props & Flash Data](/frontend/shared-data).
* Handle forms and validations: [Forms & Validation](/frontend/forms-validation).
