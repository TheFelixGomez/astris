---
layout: home

hero:
  name: "Astris"
  text: "The modern full-stack web framework for Python."
  tagline: "Full-stack simplicity with modern Python performance. Everything you need to go from idea to orbit."
  image:
    src: /astris-logo-name.png
    alt: Astris
  actions:
    - theme: brand
      text: Get Started →
      link: /getting-started/introduction
    - theme: alt
      text: View on GitHub
      link: https://github.com/TheFelixGomez/astris

features:
  - icon: ⚡
    title: Lightning-Fast Core
    details: Powered by FastAPI, Uvicorn, and Python 3.11+ async concurrency with automatic OpenAPI interactive documentation.
  - icon: 🧩
    title: Modern Monolith with Inertia.js
    details: Build rich, reactive Vue 3 SPAs directly from server-side controllers with zero client-side REST boilerplate.
  - icon: 🛡️
    title: Production-Ready Auth
    details: Cryptographically signed cookie sessions, OWASP-standard Argon2id password hashing, and complete starter kits out of the box.
  - icon: 🗄️
    title: SQLModel & Alembic Database
    details: Unified declarative models, Pydantic type safety, and automatic database migrations managed by Orbit CLI.
  - icon: 🪐
    title: Orbit Developer CLI
    details: An artisan developer CLI for scaffolding modules, generating migrations, and serving full-stack apps with hot-reloading.
  - icon: 🎨
    title: Tailwind CSS v4 Pre-configured
    details: Instant zero-config styling with Vite HMR and modern reactive components.
---

<div class="tip custom-block" style="margin-top: 2rem;">
  <p class="custom-block-title">🚀 Quick Start</p>
  <p>Create a full-stack Astris application in seconds with <code>uvx</code>:</p>
  <div class="language-bash">
    <pre><code>uvx --from astris-python astris new my_app
cd my_app
npm install
uv run orbit serve</code></pre>
  </div>
</div>
