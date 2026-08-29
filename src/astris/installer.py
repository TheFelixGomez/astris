import io
import subprocess
import sys
from pathlib import Path

import typer

if sys.platform == "win32":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

installer_cli = typer.Typer(
    name="astris",
    help="Astris Framework Installer",
    no_args_is_help=True,
    add_completion=False,
    invoke_without_command=True,
)


@installer_cli.callback()
def callback():
    """Astris Framework Installer."""


@installer_cli.command()
def new(
    name: str = typer.Argument(..., help="The name of the new project directory"),
    local_path: str | None = typer.Option(
        None, "--local", "-l", help="Path to local Astris repo for development"
    ),
    auth: bool = typer.Option(
        True,
        "--auth/--no-auth",
        help="Scaffold full-stack authentication starter kit (default: enabled)",
    ),
):
    """Scaffold a brand-new Astris full-stack project."""
    project_dir = Path.cwd() / name

    if project_dir.exists():
        typer.secho(f"Error: Directory '{name}' already exists!", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho(
        f"🚀 Crafting your Astris application: {name}", fg=typer.colors.CYAN, bold=True
    )

    # 1. Directory layout (Domain Driven + Full-Stack Resources)
    core_dir = project_dir / "app" / "core"
    shared_dir = project_dir / "app" / "shared"
    modules_dir = project_dir / "app" / "modules"
    welcome_module_dir = modules_dir / "welcome"
    database_dir = project_dir / "database" / "migrations"
    public_dir = project_dir / "public"
    views_dir = project_dir / "resources" / "views"
    css_dir = project_dir / "resources" / "css"
    js_dir = project_dir / "resources" / "js"
    pages_dir = js_dir / "Pages"
    components_dir = js_dir / "Components"

    for directory in [
        core_dir,
        shared_dir,
        welcome_module_dir,
        database_dir,
        public_dir,
        views_dir,
        css_dir,
        js_dir,
        pages_dir,
        components_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    (project_dir / "app" / "__init__.py").touch()
    (core_dir / "__init__.py").touch()
    (shared_dir / "__init__.py").touch()
    (modules_dir / "__init__.py").touch()
    (welcome_module_dir / "__init__.py").touch()

    # Default framework favicon
    try:
        import importlib.resources as pkg_resources

        favicon_bytes = (
            pkg_resources.files("astris.assets").joinpath("favicon.ico").read_bytes()
        )
        (public_dir / "favicon.ico").write_bytes(favicon_bytes)
    except (ImportError, OSError, TypeError):
        local_favicon = Path(__file__).parent / "assets" / "favicon.ico"
        if local_favicon.exists():
            (public_dir / "favicon.ico").write_bytes(local_favicon.read_bytes())

    from astris.database.migrations import ensure_migration_setup

    ensure_migration_setup(project_dir)

    # 1b. Centralized settings: app/core/config.py
    config_stub = """from astris.config import Settings as BaseAppSettings


class Settings(BaseAppSettings):
    \"\"\"Extend application settings with custom environment variables.\"\"\"

    # Add custom settings here (e.g. STRIPE_KEY, REDIS_URL, etc.)
    pass


settings = Settings()
"""
    (core_dir / "config.py").write_text(config_stub, encoding="utf-8")

    import secrets

    # 2. Environment configuration (.env and .env.example)
    app_key = secrets.token_urlsafe(32)
    env_content = f"""APP_NAME={name}
APP_ENV=local
APP_DEBUG=true
APP_KEY={app_key}

DATABASE_URL=sqlite:///database/app.db
"""
    env_example_content = f"""APP_NAME={name}
APP_ENV=local
APP_DEBUG=true
APP_KEY=

DATABASE_URL=sqlite:///database/app.db
"""
    (project_dir / ".env").write_text(env_content, encoding="utf-8")
    (project_dir / ".env.example").write_text(env_example_content, encoding="utf-8")

    # 3. pyproject.toml
    pyproject_content = f'''[project]
name = "{name.lower().replace("_", "-")}"
version = "0.1.0"
description = "An Astris web application"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []
'''
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    project_readme = f"""<p align="center" style="padding: 20px 0 10px 0;">
  <a href="https://github.com/TheFelixGomez/astris">
    <img src="https://raw.githubusercontent.com/TheFelixGomez/astris/main/.github/assets/astris-logo-name.png" alt="Astris" width="380">
  </a>
</p>

<p align="center">
  <strong>The modern full-stack web framework for Python.</strong><br>
  Full-stack simplicity with modern Python performance.
</p>

---

# {name}

An application built with **Astris**.

---

## 🚀 Getting Started

### 1. Install Frontend Dependencies
```bash
npm install
```

### 2. Start Development Server
Launch the full-stack development server:
```bash
uv run orbit serve
```
Open **`http://localhost:8000`** in your browser.

---

## 🪐 Orbit CLI Commands

| Command | Description |
| :--- | :--- |
| `uv run orbit serve` | Start full-stack development server with hot-reloading |
| `uv run orbit make:module <name>` | Scaffold a complete domain module (Controller, Service, Model) |
| `uv run orbit make:controller <name>` | Generate an Astris controller |
| `uv run orbit make:model <name>` | Generate a database model |
| `uv run orbit migrate` | Run all pending database migrations |
| `uv run orbit make:migration "<message>"` | Auto-generate a new database schema migration |
| `uv run orbit key:generate` | Generate a new 32-byte secret `APP_KEY` in `.env` |

---

## 💡 Project Architecture

* **`app/modules/`**: Domain modules with controllers, models, and routes.
* **`app/core/config.py`**: Centralized application configuration.
* **`resources/js/Pages/`**: Frontend single-page application views.
* **`database/migrations/`**: Database schema migrations managed by Orbit.
* **`public/`**: Web root directory for static assets (favicon, images, robots.txt).

---

## 📖 About Astris

**Astris** is a modern full-stack web framework for Python with expressive, type-safe elegance. Designed to help developers build and ship modern web applications with speed and simplicity.

* **Documentation**: [https://astris.dev](https://astris.dev)
* **Repository**: [https://github.com/TheFelixGomez/astris](https://github.com/TheFelixGomez/astris)
* **Author**: Felix Gomez ([@TheFelixGomez](https://github.com/TheFelixGomez))
"""
    (project_dir / "README.md").write_text(project_readme, encoding="utf-8")
    (project_dir / ".gitignore").write_text(
        ".venv/\nnode_modules/\n__pycache__/\n*.pyc\n.env\npublic/build/\n",
        encoding="utf-8",
    )

    # 3. main.py entry point
    main_content = """from astris import Astris

app = Astris()
"""
    (project_dir / "main.py").write_text(main_content, encoding="utf-8")

    # 4. Default Welcome Controller using InertiaResponse
    welcome_controller = """from astris.http import Request
from astris.inertia import InertiaResponse
from astris.routing import Controller

controller = Controller(tags=["Home"])


@controller.get("/")
async def index(request: Request) -> InertiaResponse:
    return InertiaResponse(
        request,
        "Welcome",
        props={
            "status": "online",
            "message": "Welcome to your Astris application! 🚀",
            "version": "0.1.0",
            "api_docs_url": "/docs",
            "redoc_url": "/redoc",
            "docs_url": "https://astris.dev",
        },
    )
"""
    (welcome_module_dir / "welcome_controller.py").write_text(
        welcome_controller, encoding="utf-8"
    )

    # 5. Frontend: package.json
    package_json_content = f'''{{
  "name": "{name.lower().replace("_", "-")}",
  "private": true,
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build"
  }},
  "dependencies": {{
    "@inertiajs/vue3": "^3.6.1",
    "vue": "^3.5.41"
  }},
  "devDependencies": {{
    "@tailwindcss/vite": "^4.3.3",
    "@vitejs/plugin-vue": "^6.0.8",
    "tailwindcss": "^4.3.3",
    "typescript": "^7.0.2",
    "vite": "^8.2.2"
  }}
}}
'''
    (project_dir / "package.json").write_text(package_json_content, encoding="utf-8")

    # 6. Frontend: vite.config.ts
    vite_config_content = """import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";

export default defineConfig({
  plugins: [tailwindcss(), vue()],
  publicDir: false,
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "resources/js"),
    },
  },
  build: {
    outDir: "public/build",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: "resources/js/app.ts",
    },
  },
  server: {
    origin: "http://localhost:5173",
    port: 5173,
    strictPort: true,
  },
});
"""
    (project_dir / "vite.config.ts").write_text(vite_config_content, encoding="utf-8")

    # 7. Frontend: tsconfig.json
    tsconfig_content = """{
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ESNext", "DOM"],
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["resources/js/*"]
    }
  },
  "include": ["resources/js/**/*.ts", "resources/js/**/*.d.ts", "resources/js/**/*.vue"]
}
"""
    (project_dir / "tsconfig.json").write_text(tsconfig_content, encoding="utf-8")

    # 8. Frontend: resources/css/app.css (Tailwind CSS v4)
    (css_dir / "app.css").write_text('@import "tailwindcss";\n', encoding="utf-8")

    # 9. Frontend: resources/views/root.html
    root_html_content = """<!DOCTYPE html>
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
"""
    (views_dir / "root.html").write_text(root_html_content, encoding="utf-8")

    # 10. Frontend: resources/js/app.ts
    app_ts_content = """import "../css/app.css";
import { createApp, h } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";

const el = document.getElementById("app");

if (!el || !el.dataset.page) {
  throw new Error("Inertia root element (#app) or data-page attribute not found in the DOM.");
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
"""
    (js_dir / "app.ts").write_text(app_ts_content, encoding="utf-8")

    # 10. Frontend: resources/js/Components/AstrisLogo.vue
    astris_logo_vue_content = """<template>
  <svg
    viewBox="0 0 792 792"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="m50 757h88.8l37.8-92.3c-31.4-1.6-59-6.3-82.4-14.2z"/>
    <path d="m596.3 550.8q-11 6.5-22.3 12.6l79.1 193.6h88.9l-98.1-236.5q-22.4 15.6-47.6 30.3z"/>
    <path d="m210.1 582.6l185.9-454.7 147.5 360.9c25-14.4 48-29.9 68.2-46l-169.2-407.8h-93l-221.6 534.1c21.2 8.3 49.5 12.9 82.2 13.5z"/>
    <path fill-rule="evenodd" d="m372.5 466.8l23.5 76.4 23.5-76.4 69-23.5-68.8-23.8-23.7-75.8-23.7 75.8-68.8 23.8 69 23.5z"/>
    <path d="m756.2 309.9c-18.3-50.9-96.5-72.1-201.4-61.6 81.6-3.1 141.7 15.8 156.8 58 26.6 74.2-96.3 192.3-273.9 256.1-177.7 63.7-343.3 55.2-370-19-15.5-43.4 19.7-99.6 87.1-151.5-90.4 60.9-137.6 131.1-118.9 183.2 29.4 82 214.3 90.6 413.1 19.3 198.8-71.3 336.6-202.5 307.2-284.5z"/>
    <path d="m90 533.2c2.1 6 5.3 11.5 9.4 16.6q-2.3-3.9-3.9-8.2c-12.7-35.5 18.2-82.5 77.1-127.1l12.8-31c-71.7 50.7-110.7 107.1-95.4 149.7z"/>
    <path d="m437 275.7c-30 6.8-61.1 15.9-92.6 27.2q-0.3 0.1-0.6 0.2l-10.1 24.7q8.5-3.3 17.3-6.4c31.8-11.4 63.2-20.7 93.3-27.8l-7.4-17.9z"/>
    <path d="m688.7 323.7q1.4 4.1 2.1 8.4c0-6.6-1.1-12.9-3.2-18.9-13.1-36.3-63.2-53.7-132.2-52.9l7 16.8c66.6-1.8 114.4 13.4 126.3 46.6z"/>
  </svg>
</template>
"""
    (components_dir / "AstrisLogo.vue").write_text(
        astris_logo_vue_content, encoding="utf-8"
    )

    # 11. Frontend: resources/js/Pages/Welcome.vue
    welcome_vue_content = """<script setup lang="ts">
import { Link, usePage } from '@inertiajs/vue3';
import AstrisLogo from '../Components/AstrisLogo.vue';

interface Props {
  status: string;
  message: string;
  version?: string;
  api_docs_url?: string;
  redoc_url?: string;
  docs_url?: string;
}

withDefaults(defineProps<Props>(), {
  version: "0.1.0",
  api_docs_url: "/docs",
  redoc_url: "/redoc",
  docs_url: "https://github.com/TheFelixGomez/astris",
});

const page = usePage();
</script>

<template>
  <main class="min-h-screen flex flex-col justify-between bg-slate-950 text-slate-100 p-6 font-sans relative overflow-hidden selection:bg-sky-500 selection:text-white">
    <!-- Subtle Background Ambient Glow -->
    <div class="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-sky-500/10 blur-[120px] rounded-full pointer-events-none -z-10"></div>

    <!-- Top Navigation -->
    <header class="flex justify-between items-center max-w-5xl w-full mx-auto py-2">
      <div class="flex items-center gap-2.5">
        <AstrisLogo class="w-8 h-8 text-sky-400" />
        <span class="font-bold text-lg tracking-tight text-white">Astris</span>
      </div>

      <nav class="flex items-center gap-3">
        <template v-if="page.props.auth?.user">
          <Link
            href="/dashboard"
            class="px-4 py-2 rounded-xl text-sm font-medium text-sky-400 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 hover:border-sky-500/40 transition duration-200"
          >
            Dashboard &rarr;
          </Link>
        </template>
        <template v-else>
          <Link
            href="/login"
            class="px-3.5 py-1.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white transition duration-200"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            class="px-4 py-1.5 rounded-xl text-sm font-medium text-white bg-sky-500 hover:bg-sky-400 shadow-md shadow-sky-500/20 transition duration-200"
          >
            Register
          </Link>
        </template>
      </nav>
    </header>

    <!-- Main Hero Content -->
    <div class="max-w-3xl w-full my-auto mx-auto text-center py-10">
      <!-- Hero Logo & Title -->
      <div class="mb-10 flex flex-col items-center">
        <div class="relative mb-6 group">
          <div class="absolute -inset-2 bg-gradient-to-r from-sky-500 to-indigo-500 rounded-3xl blur-lg opacity-30 group-hover:opacity-60 transition duration-500"></div>
          <div class="relative p-4 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur shadow-2xl">
            <AstrisLogo class="w-16 h-16 text-sky-400" />
          </div>
        </div>

        <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-3">
          Astris
        </h1>
        <p class="text-lg sm:text-xl text-slate-400 max-w-xl mx-auto leading-relaxed mb-5">
          {{ message }}
        </p>

        <!-- Version & Status Badge -->
        <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-300 shadow-sm backdrop-blur">
          <span class="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse"></span>
          <span>Status: <span class="text-emerald-400 font-semibold">{{ status }}</span></span>
          <span class="text-slate-600">&bull;</span>
          <span class="text-sky-400">v{{ version }}</span>
        </div>
      </div>

      <!-- Quick Navigation Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left mb-10">
        <!-- Interactive API Docs -->
        <a
          :href="api_docs_url"
          target="_blank"
          rel="noopener noreferrer"
          class="group p-5 rounded-2xl bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 backdrop-blur shadow-lg transition-all duration-200 hover:-translate-y-1"
        >
          <div class="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-lg mb-3.5 group-hover:scale-110 transition duration-200">
            ⚡
          </div>
          <h3 class="text-sm font-semibold text-white mb-1 group-hover:text-sky-400 transition">Swagger API Docs</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Interactive OpenAPI interface to explore and test endpoints.</p>
        </a>

        <!-- ReDoc API Docs -->
        <a
          :href="redoc_url"
          target="_blank"
          rel="noopener noreferrer"
          class="group p-5 rounded-2xl bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 backdrop-blur shadow-lg transition-all duration-200 hover:-translate-y-1"
        >
          <div class="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-lg mb-3.5 group-hover:scale-110 transition duration-200">
            📑
          </div>
          <h3 class="text-sm font-semibold text-white mb-1 group-hover:text-sky-400 transition">ReDoc Schema</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Clean, structured documentation for API schemas and models.</p>
        </a>

        <!-- Project / Framework Documentation -->
        <a
          :href="docs_url"
          target="_blank"
          rel="noopener noreferrer"
          class="group p-5 rounded-2xl bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 backdrop-blur shadow-lg transition-all duration-200 hover:-translate-y-1"
        >
          <div class="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-lg mb-3.5 group-hover:scale-110 transition duration-200">
            📖
          </div>
          <h3 class="text-sm font-semibold text-white mb-1 group-hover:text-sky-400 transition">Astris Docs</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Official guides, controllers, Inertia integration, and tutorials.</p>
        </a>
      </div>

      <!-- Quick Command Tip -->
      <div class="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs font-mono text-slate-400 flex items-center justify-center gap-2 shadow-inner">
        <span>Get started:</span>
        <code class="text-sky-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">uv run orbit make:module billing</code>
        <span class="text-slate-600">&bull;</span>
        <code class="text-indigo-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">uv run orbit serve</code>
      </div>
    </div>

    <!-- Footer -->
    <footer class="text-center text-xs text-slate-500 py-4">
      Built with ❤️ by <a href="https://github.com/TheFelixGomez" target="_blank" rel="noopener noreferrer" class="text-slate-400 hover:text-slate-300 underline underline-offset-4 transition">Felix Gomez</a>.
    </footer>
  </main>
</template>
"""
    (pages_dir / "Welcome.vue").write_text(welcome_vue_content, encoding="utf-8")

    if auth:
        from astris.auth.installer import install_auth_starter

        install_auth_starter(project_dir)
        typer.secho(
            "✓ Scaffolded full-stack authentication starter kit", fg=typer.colors.GREEN
        )

    # 11. Initialize Python virtualenv and resolve dependencies
    typer.echo("📦 Initializing virtual environment and resolving dependencies...")
    subprocess.run(["uv", "venv"], cwd=project_dir, check=True)

    if local_path:
        resolved_local = str(Path(local_path).resolve())
        subprocess.run(["uv", "add", resolved_local], cwd=project_dir, check=True)
    else:
        sibling_astris = (Path.cwd() / "astris").resolve()
        parent_astris = (Path.cwd() / ".." / "astris").resolve()

        if (sibling_astris / "pyproject.toml").exists():
            subprocess.run(
                ["uv", "add", str(sibling_astris)], cwd=project_dir, check=True
            )
        elif (parent_astris / "pyproject.toml").exists():
            subprocess.run(
                ["uv", "add", str(parent_astris)], cwd=project_dir, check=True
            )
        else:
            subprocess.run(["uv", "add", "astris-python"], cwd=project_dir, check=True)

    typer.secho(
        f"\n✓ Project {name} created successfully!", fg=typer.colors.GREEN, bold=True
    )
    typer.echo("\nTo get started, run:")
    typer.secho(f"  cd {name}", fg=typer.colors.YELLOW)
    typer.secho("  npm install", fg=typer.colors.YELLOW)
    typer.secho("  uv run orbit serve\n", fg=typer.colors.YELLOW)
