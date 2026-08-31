# Installation & Quickstart

Creating an Astris application takes less than 30 seconds.

## Prerequisites

Before creating your first Astris project, ensure you have the following installed:

1. **[Python 3.11+](https://www.python.org/downloads/)** (Python 3.14 recommended, or install via `uv python install 3.14`)
2. **[uv](https://docs.astral.sh/uv/)** (recommended for ultra-fast Python package management):
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS & Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **[Node.js](https://nodejs.org/)** version `^22.18.0` or `>=24.12.0` (Node 24 LTS recommended) & npm.

## Getting Started Using AI

If you build with AI coding assistants (such as Claude Code, Cursor, GitHub Copilot, Antigravity, or OpenCode), you can prime your agent with the official Astris playbook before writing your first line of code.

This equips your assistant with Astris's full-stack architecture, domain-driven conventions, and Orbit CLI commands. Paste this into your agent to get started:

```text
I'm building a new Astris application.

Fetch and follow the instructions from https://astris.dev/for/agents. Treat the returned Markdown as the source of truth for how to install, set up, and develop with Astris in this session.
```

After the agent reads the instructions, it will guide you step by step and keep the setup aligned with Astris's conventions and defaults.

## Creating a New Project

### Method 1: Zero-Install with `uvx` (Recommended)

Run `astris new` directly without pre-installing anything globally:

```bash
uvx --from astris-python astris new my_app
```

### Method 2: Global CLI Installation

Install the `astris` CLI globally on your system:

```bash
# Install with uv tool
uv tool install astris-python

# Or with pipx
pipx install astris-python
```

Once installed globally, you can create new projects anytime:

```bash
astris new my_app
```

::: tip Full-Stack Auth Included
Every Astris project comes pre-configured with a full-stack authentication system (Login, Registration, Argon2id Password Hashing, Session Guards, and Dashboard UI). If you want to scaffold a minimal project without authentication, pass `--no-auth`:

```bash
uvx --from astris-python astris new my_app --no-auth
```
:::

## Running the Application

Navigate into your newly created project directory:

```bash
cd my_app
```

### 1. Install Frontend Dependencies
```bash
npm install
```

### 2. Start Full-Stack Development Server
```bash
uv run orbit serve
```

Astris launches your FastAPI backend on `http://localhost:8000` and concurrently starts the Vite Hot Module Replacement (HMR) server for Vue 3 and Tailwind CSS.

Open **`http://localhost:8000`** in your browser!

## Interactive API Documentation

Every Astris application automatically provides interactive OpenAPI documentation out of the box:

* **Swagger UI**: `http://localhost:8000/docs`
* **ReDoc Schema**: `http://localhost:8000/redoc`

## Next Steps

* Explore your project layout: [Directory Structure](/getting-started/directory-structure).
* Learn about settings & `.env`: [Configuration](/getting-started/configuration).
