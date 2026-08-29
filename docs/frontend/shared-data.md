# Shared Props & Flash Data

Shared props allow you to make global data (such as authenticated users, global settings, flash messages, and CSRF tokens) available across **every Vue component** via `$page.props`.

## Global Shared Data (`share()`)

To register global shared props that are evaluated on every request, use `share()`:

```python
from astris.inertia import share

# Share static data
share("app_name", "Astris Platform")

# Or share dynamic callable data
share("auth", lambda request: {
    "user": getattr(request.state, "user", None)
})
```

## Accessing Shared Props in Vue 3

Inside any Vue 3 component or layout:

```vue
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3'

const page = usePage()

// Access global shared props
const user = page.props.auth?.user
const appName = page.props.app_name
</script>

<template>
  <nav>
    <span>{{ appName }}</span>
    <span v-if="user">Logged in as {{ user.name }}</span>
  </nav>
</template>
```

## Flash Messages (`flash()`)

Flash messages are short notifications stored temporarily in session cookies and cleared immediately after being displayed.

### Setting Flash Data in Python:

```python
from astris.inertia import flash, InertiaResponse
from astris.http import Request, RedirectResponse, status

@controller.post("/settings")
async def update_settings(request: Request) -> RedirectResponse:
    # Perform update logic...
    flash(request, "success", "Profile updated successfully!")
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)
```

### Displaying Flash Messages in Vue 3:

```vue
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3'

const page = usePage()
</script>

<template>
  <div>
    <!-- Success Banner -->
    <div
      v-if="page.props.flash?.success"
      class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
    >
      {{ page.props.flash.success }}
    </div>

    <!-- Error Banner -->
    <div
      v-if="page.props.flash?.error"
      class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400"
    >
      {{ page.props.flash.error }}
    </div>
  </div>
</template>
```

## Next Steps

* Master form handling and validation errors: [Forms & Validation](/frontend/forms-validation).
* Configure Vite and styling: [Vite & Tailwind CSS v4](/frontend/vite-tailwind).
