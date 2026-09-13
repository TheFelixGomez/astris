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

::: details Step-by-step breakdown

### Step 1: Import `share`

```python
from astris.inertia import share
```

Imports the global sharing registry function from Astris's Inertia module.

### Step 2: Share static data

```python
share("app_name", "Astris Platform")
```

Registers a static prop named `"app_name"`. Every Inertia response rendered across your entire application will automatically include `props.app_name = "Astris Platform"`.

### Step 3: Share dynamic callable data

```python
share("auth", lambda request: {
    "user": getattr(request.state, "user", None)
})
```

* By passing a function or `lambda` that accepts `request`, the prop is evaluated lazily at the moment each response is rendered.
* `getattr(request.state, "user", None)` safely pulls the authenticated user attached by your authentication guards or session middleware.
* If no user is logged in, it cleanly evaluates to `None` without crashing.

:::

## Accessing Shared Props in Vue 3

Inside any Vue 3 component or layout, access shared data via Inertia's `usePage()` hook:

```vue
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3'

const page = usePage()

// Access global shared props
const user = page.props.auth?.user
const appName = page.props.app_name
</script>

<template>
  <nav class="flex justify-between items-center p-4">
    <span class="font-bold">{{ appName }}</span>
    <span v-if="user">Logged in as {{ user.name }}</span>
    <span v-else>Guest</span>
  </nav>
</template>
```

::: details Vue 3 usage breakdown

* **`import { usePage } from '@inertiajs/vue3'`**: Imports the page object containing current route metadata and all shared props.
* **`const page = usePage()`**: Grants reactive access to the page context.
* **`page.props.auth?.user`**: Accesses the shared `auth` object. Using optional chaining (`?.`) ensures your template renders smoothly when a visitor is logged out.

:::

## Flash Messages (`flash()`)

Flash messages are short notifications stored temporarily in session cookies and cleared immediately after being displayed.

### Setting Flash Data in Python

```python
from astris.inertia import flash
from astris.http import Request, RedirectResponse, status

@controller.post("/settings")
async def update_settings(request: Request) -> RedirectResponse:
    # 1. Perform update logic...

    # 2. Flash a success notification
    flash(request, "success", "Profile updated successfully!")

    # 3. Redirect back with 303 See Other
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)
```

::: details Flash lifecycle breakdown

1. **`flash(request, "success", "...")`**: Writes the message into `request.session["_flash"]`. The message is encrypted and signed inside the session cookie using your `APP_KEY`.
2. **`RedirectResponse(..., status_code=status.HTTP_303_SEE_OTHER)`**: Redirects the browser to the destination URL.
3. **Automatic Consumption**: During the subsequent `GET` request, Astris's `FlashMiddleware` extracts the message into `request.state.flash` and automatically deletes it from the session cookie so it is never displayed twice.

:::

### Displaying Flash Messages in Vue 3

In your root layout or notification component:

```vue
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3'

const page = usePage()
</script>

<template>
  <div class="space-y-3">
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

#### How the Template Reacts

* **`page.props.flash?.success`**: Astris automatically shares all flash messages on the `flash` key of `$page.props`.
* **Automatic Dismissal**: When the user clicks to navigate to another page, Inertia fetches the next page without flash data, causing the banner to disappear seamlessly.

## Next Steps

* Master form handling and validation errors: [Forms & Validation](/frontend/forms-validation).
* Configure Vite and styling: [Vite & Tailwind CSS v4](/frontend/vite-tailwind).
