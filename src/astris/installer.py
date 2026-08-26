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
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    (project_dir / "app" / "__init__.py").touch()
    (core_dir / "__init__.py").touch()
    (shared_dir / "__init__.py").touch()
    (modules_dir / "__init__.py").touch()
    (welcome_module_dir / "__init__.py").touch()

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
    (project_dir / "README.md").write_text(
        f"# {name}\n\nBuilt with Astris + Inertia + Vue 3.", encoding="utf-8"
    )
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
            "docs_url": "https://astris.dev/docs",
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

    # 10. Frontend: resources/js/Pages/Welcome.vue
    welcome_vue_content = """<script setup lang="ts">
import { Link, usePage } from '@inertiajs/vue3';

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
  docs_url: "https://astris.dev/docs",
});

const page = usePage();
</script>

<template>
  <main style="min-height: 100vh; display: flex; flex-direction: column; justify-content: space-between; background: #090d16; color: #f8fafc; padding: 1.5rem; font-family: system-ui, -apple-system, sans-serif;">
    <!-- Top Auth Navigation -->
    <header style="display: flex; justify-content: flex-end; gap: 1rem; max-width: 64rem; width: 100%; margin: 0 auto;">
      <template v-if="page.props.auth?.user">
        <Link
          href="/dashboard"
          style="padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #38bdf8; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); text-decoration: none; transition: all 0.2s;"
        >
          Dashboard &rarr;
        </Link>
      </template>
      <template v-else>
        <Link
          href="/login"
          style="padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #94a3b8; text-decoration: none; transition: color 0.2s;"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          style="padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #ffffff; background: #2563eb; text-decoration: none; transition: background 0.2s;"
        >
          Register
        </Link>
      </template>
    </header>

    <div style="max-width: 48rem; width: 100%; margin: 2rem auto; text-align: center;">
      <!-- Hero Header -->
      <div style="margin-bottom: 2.5rem;">
        <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: -0.025em; margin: 0 0 0.5rem 0; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          Astris
        </h1>
        <p style="font-size: 1.125rem; color: #94a3b8; margin: 0 0 1.25rem 0;">
          {{ message }}
        </p>
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.85rem; border-radius: 9999px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.2); color: #38bdf8; font-size: 0.8125rem; font-family: monospace;">
          <span style="width: 0.5rem; height: 0.5rem; border-radius: 9999px; background: #22c55e; box-shadow: 0 0 8px #22c55e;"></span>
          Status: {{ status }} &bull; v{{ version }}
        </div>
      </div>

      <!-- Quick Navigation Cards -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; text-align: left; margin-bottom: 2.5rem;">
        <!-- Interactive API Docs -->
        <a
          :href="api_docs_url"
          target="_blank"
          rel="noopener noreferrer"
          style="display: block; padding: 1.25rem; border-radius: 0.75rem; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.1); color: inherit; text-decoration: none; transition: border-color 0.2s, transform 0.2s;"
          onmouseover="this.style.borderColor='rgba(56,189,248,0.4)'; this.style.transform='translateY(-2px)';"
          onmouseout="this.style.borderColor='rgba(148,163,184,0.1)'; this.style.transform='none';"
        >
          <div style="font-size: 1.25rem; margin-bottom: 0.5rem;">⚡</div>
          <h3 style="font-size: 1rem; font-weight: 600; margin: 0 0 0.25rem 0; color: #f1f5f9;">Swagger API Docs</h3>
          <p style="font-size: 0.8125rem; color: #94a3b8; margin: 0;">Interactive OpenAPI interface to explore and test endpoints.</p>
        </a>

        <!-- ReDoc API Docs -->
        <a
          :href="redoc_url"
          target="_blank"
          rel="noopener noreferrer"
          style="display: block; padding: 1.25rem; border-radius: 0.75rem; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.1); color: inherit; text-decoration: none; transition: border-color 0.2s, transform 0.2s;"
          onmouseover="this.style.borderColor='rgba(129,140,248,0.4)'; this.style.transform='translateY(-2px)';"
          onmouseout="this.style.borderColor='rgba(148,163,184,0.1)'; this.style.transform='none';"
        >
          <div style="font-size: 1.25rem; margin-bottom: 0.5rem;">📑</div>
          <h3 style="font-size: 1rem; font-weight: 600; margin: 0 0 0.25rem 0; color: #f1f5f9;">ReDoc Schema</h3>
          <p style="font-size: 0.8125rem; color: #94a3b8; margin: 0;">Clean, structured documentation for API schemas and models.</p>
        </a>

        <!-- Project / Framework Documentation -->
        <a
          :href="docs_url"
          target="_blank"
          rel="noopener noreferrer"
          style="display: block; padding: 1.25rem; border-radius: 0.75rem; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.1); color: inherit; text-decoration: none; transition: border-color 0.2s, transform 0.2s;"
          onmouseover="this.style.borderColor='rgba(192,132,252,0.4)'; this.style.transform='translateY(-2px)';"
          onmouseout="this.style.borderColor='rgba(148,163,184,0.1)'; this.style.transform='none';"
        >
          <div style="font-size: 1.25rem; margin-bottom: 0.5rem;">📖</div>
          <h3 style="font-size: 1rem; font-weight: 600; margin: 0 0 0.25rem 0; color: #f1f5f9;">Astris Docs</h3>
          <p style="font-size: 0.8125rem; color: #94a3b8; margin: 0;">Official guides, controllers, Inertia integration, and tutorials.</p>
        </a>
      </div>

      <!-- Quick Command Tip -->
      <div style="padding: 0.875rem 1.25rem; border-radius: 0.5rem; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.08); font-size: 0.8125rem; color: #64748b; font-family: monospace;">
        Get started: <span style="color: #38bdf8;">uv run orbit make:module billing</span> &bull; <span style="color: #818cf8;">uv run orbit serve</span>
      </div>
    </div>

    <!-- Footer placeholder for layout balance -->
    <footer style="text-align: center; font-size: 0.75rem; color: #475569;">
      Built with ❤️ by <a href="https://github.com/TheFelixGomez" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline;">Felix Gomez</a>.
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
