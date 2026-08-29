# Forms & Validation

Astris and Inertia.js provide a seamless form-handling workflow. When validation fails on the server, Astris automatically flashes error messages and redirects back to the previous page with zero client-side boilerplate.

## Form Handling in Vue 3 (`useForm`)

Use Inertia's `useForm` helper to bind form inputs, track processing states, and display validation errors:

```vue
<script setup lang="ts">
import { useForm } from '@inertiajs/vue3'

const form = useForm({
  title: '',
  content: '',
})

const submit = () => {
  form.post('/articles', {
    onSuccess: () => form.reset(),
  })
}
</script>

<template>
  <form @submit.prevent="submit" class="space-y-4">
    <!-- Title Input -->
    <div>
      <label class="block text-sm font-medium">Title</label>
      <input
        v-model="form.title"
        type="text"
        class="w-full px-3 py-2 border rounded-xl bg-slate-800 text-white"
        :class="{ 'border-rose-500': form.errors.title }"
      />
      <p v-if="form.errors.title" class="text-sm text-rose-400 mt-1">
        {{ form.errors.title }}
      </p>
    </div>

    <!-- Content Input -->
    <div>
      <label class="block text-sm font-medium">Content</label>
      <textarea
        v-model="form.content"
        rows="4"
        class="w-full px-3 py-2 border rounded-xl bg-slate-800 text-white"
      ></textarea>
      <p v-if="form.errors.content" class="text-sm text-rose-400 mt-1">
        {{ form.errors.content }}
      </p>
    </div>

    <button
      type="submit"
      :disabled="form.processing"
      class="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold disabled:opacity-50"
    >
      <span v-if="form.processing">Saving...</span>
      <span v-else>Create Article</span>
    </button>
  </form>
</template>
```

## Server-Side Validation in Python

Validate incoming requests using Pydantic or SQLModel schemas:

```python
from astris.routing import Controller
from astris.http import Request, RedirectResponse, status
from pydantic import BaseModel, Field

controller = Controller(prefix="/articles")


class ArticleCreateDTO(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=10)


@controller.post("/")
async def store(request: Request, dto: ArticleCreateDTO) -> RedirectResponse:
    # Validation is executed automatically before this function runs.
    # If invalid, Astris automatically intercepts the 422 error,
    # flashes errors into $page.props.errors, and redirects back via 303.
    
    # Save to database...
    
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
```

## Redirecting After Form Submission

After processing a mutating request (`POST`, `PUT`, `PATCH`, or `DELETE`) in your controller, return a `RedirectResponse` with a **`303 See Other`** status code:

```python
from astris.http import RedirectResponse, status

@controller.post("/")
async def store(request: Request, dto: ArticleCreateDTO) -> RedirectResponse:
    # 1. Save to database...

    # 2. Redirect to the target page
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
```

### Why `303 See Other`?

Inertia.js uses standard HTTP redirect semantics to drive its single-page application navigation:
* **Forces a `GET` request**: Unlike a `302` or `307` redirect (which can preserve the original HTTP method), a `303 See Other` explicitly instructs the browser and Inertia client to follow the redirect as a **`GET`** request to load the new page view.
* **Prevents Duplicate Submissions**: It eliminates the dreaded "Confirm Form Resubmission" dialog if the user refreshes their browser.

::: tip Automatic Validation Error Handling
If validation fails on the server, you don't need to write any error-handling code. Astris automatically intercepts invalid inputs, flashes field errors into session state, and redirects back to the previous page where `form.errors` is hydrated in Vue immediately.
:::

## Next Steps

* Build frontend assets: [Vite & Tailwind CSS v4](/frontend/vite-tailwind).
* Configure database persistence: [Database Configuration](/database/configuration).
