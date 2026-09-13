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

::: details How `useForm` works in Vue 3

* **Import `useForm`**:
  ```typescript
  import { useForm } from '@inertiajs/vue3'
  ```
  Provides a reactive form helper that tracks inputs, errors, and loading states.
* **Initialize reactive state**:
  ```typescript
  const form = useForm({
    title: '',
    content: '',
  })
  ```
  Creates reactive properties (`form.title`, `form.content`), loading states (`form.processing`), and error messages (`form.errors`).
* **Submit the form**:
  ```typescript
  form.post('/articles', {
    onSuccess: () => form.reset(),
  })
  ```
  Sends an asynchronous `POST` request with the CSRF token attached automatically. `form.reset()` clears all fields when successful.
* **Display validation errors**:
  ```vue
  <input
    v-model="form.title"
    :class="{ 'border-rose-500': form.errors.title }"
  />
  <p v-if="form.errors.title">{{ form.errors.title }}</p>
  ```
  Conditionally highlights the border and displays the server error message.
* **Prevent duplicate submissions**:
  ```vue
  <button type="submit" :disabled="form.processing">
  ```
  Disables the button automatically while the request is in-flight.

:::

## Server-Side Validation in Python

Validate incoming requests using Pydantic or SQLModel schemas:

```python
from astris.routing import Controller
from astris.http import Request, RedirectResponse, status
from pydantic import BaseModel, Field

controller = Controller(prefix="/articles")


class ArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=10)


@controller.post("/")
async def store(request: Request, dto: ArticleCreate) -> RedirectResponse:
    # 1. Validation runs automatically before this function body executes.
    # 2. If valid, save to database:
    #    article = Article.model_validate(dto)
    #    db.add(article)

    # 3. Return a 303 redirect to the target page
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
```

::: details Step-by-step breakdown

### Step 1: Define the validation schema

```python
class ArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=10)
```

* `title`: Requires a string between 3 and 100 characters.
* `content`: Requires a string with at least 10 characters.

### Step 2: Accept the schema in your controller

```python
@controller.post("/")
async def store(request: Request, dto: ArticleCreate) -> RedirectResponse:
```

Astris parses the incoming request body and validates it against `ArticleCreate`. If validation passes, `dto` is injected as a typed instance into your function. If validation fails, Astris raises a `422 Unprocessable Entity` error.

:::

::: details How Astris automates validation errors

When validation fails (e.g., the title is only 1 character long):
1. Astris detects the validation failure and generates an HTTP 422 response.
2. Astris's built-in Inertia exception handler intercepts the 422 error.
3. It extracts the error messages into a flat dictionary (e.g. `{"title": "String should have at least 3 characters"}`).
4. It flashes this dictionary into session state and immediately responds with a **`303 See Other`** redirect back to the previous page.
5. On the previous page, Inertia populates `form.errors` with these exact messages without full-page reloads.

:::

## Redirecting After Form Submission

After processing a mutating request (`POST`, `PUT`, `PATCH`, or `DELETE`) in your controller, return a `RedirectResponse` with a **`303 See Other`** status code:

```python
from astris.http import RedirectResponse, status

@controller.post("/")
async def store(request: Request, dto: ArticleCreate) -> RedirectResponse:
    # 1. Save to database...

    # 2. Redirect to the target page
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
```

::: details Why HTTP 303 is required for Inertia

Inertia.js uses standard HTTP redirect semantics to drive its single-page application navigation:
* **Forces a `GET` request**: Unlike a `302` or `307` redirect (which can preserve the original HTTP method), a `303 See Other` explicitly instructs the browser and Inertia client to follow the redirect as a **`GET`** request to load the new page view.
* **Prevents Duplicate Submissions**: It eliminates the dreaded "Confirm Form Resubmission" dialog if the user refreshes their browser.

:::

::: tip Zero Error Boilerplate
You never need to write manual `try/except` blocks or parse validation errors in your controllers. Astris handles validation failure, flash message persistence, and page redirection entirely behind the scenes.
:::

## Next Steps

* Build frontend assets: [Vite & Tailwind CSS v4](/frontend/vite-tailwind).
* Configure database persistence: [Database Configuration](/database/configuration).
