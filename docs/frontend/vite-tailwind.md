# Vite & Tailwind CSS v4

Astris comes pre-configured with **Vite** and **Tailwind CSS v4** for instant Hot Module Replacement (HMR) during development and optimized bundling in production.

## Vite Configuration (`vite.config.ts`)

Every Astris application contains a streamlined `vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./resources/js"),
    },
  },
  build: {
    outDir: "public/build",
    manifest: "manifest.json",
    rollupOptions: {
      input: "resources/js/app.ts",
    },
  },
});
```

## Tailwind CSS v4

Astris uses Tailwind CSS v4 via `@tailwindcss/vite`.

Your stylesheet in `resources/css/app.css` only requires a single directive:

```css
@import "tailwindcss";
```

No `tailwind.config.js` or `postcss.config.js` files are needed.

## Public Static Assets (`public/`)

The `public/` directory is treated as your application's static web root:

```text
public/
├── favicon.ico
├── robots.txt
└── images/
    └── logo.png
```

* Any file placed inside `public/` is served directly at the root URL (e.g. `http://localhost:8000/favicon.ico` or `/images/logo.png`).
* Astris's `PublicStaticMiddleware` handles static asset delivery with built-in path-traversal protection.

## Next Steps

* Connect to your database: [Database Configuration](/database/configuration).
* Create SQLModel schemas: [SQLModel Models](/database/models).
