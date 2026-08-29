# Inertia.js Overview

[Inertia.js](https://inertiajs.com/) lets you build single-page apps (SPAs) without building client-side APIs.

## The Inertia Paradigm

In a standard SPA architecture:
1. You build a client-side routing system (Vue Router).
2. You create client-side API calls with Axios or Fetch.
3. You duplicate state and validation schemas on both backend and frontend.

**With Astris + Inertia:**
* You use classic server-side routing and controllers in Python.
* Your controllers return Vue 3 page components with props.
* Inertia intercepts link clicks and form submissions via XHR, replacing the page component in the DOM **without full page reloads**.

```text
User clicks <Link href="/users">
             │
             ▼
FastAPI Controller executes in Python
             │
             ▼
Returns InertiaResponse(request, "Users", props={"users": [...]})
             │
             ▼
Inertia swaps DOM with Users.vue & hydrates $page.props
```

## The Client Entrypoint (`resources/js/app.ts`)

Inertia boots inside `resources/js/app.ts`:

```typescript
import "../css/app.css";
import { createApp, h } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";

const el = document.getElementById("app");

if (!el || !el.dataset.page) {
  throw new Error("Inertia root element (#app) not found.");
}

const initialPage = JSON.parse(el.dataset.page);
const pages = import.meta.glob("./Pages/**/*.vue", { eager: true });

createInertiaApp({
  page: initialPage,
  resolve: (name) => {
    const page: any = pages[`./Pages/${name}.vue`];
    if (!page) {
      throw new Error(`Page component "${name}" not found in ./Pages/`);
    }
    return page.default ?? page;
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el);
  },
});
```

## Next Steps

* Learn how to render pages: [Rendering Responses](/frontend/responses).
* Share global data with Vue: [Shared Props & Flash Data](/frontend/shared-data).
