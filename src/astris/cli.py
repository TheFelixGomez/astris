import io
import subprocess
import sys
from pathlib import Path

import typer
import uvicorn

if sys.platform == "win32":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

orbit_cli = typer.Typer(
    name="orbit",
    help="Astris CLI",
    no_args_is_help=True,
    add_completion=False,
)


@orbit_cli.command("list")
def list_commands(ctx: typer.Context):
    """List all available Orbit commands."""
    if ctx.parent:
        typer.echo(ctx.parent.get_help())
    else:
        typer.echo(ctx.get_help())


@orbit_cli.command()
def serve(
    host: str = typer.Option(
        "127.0.0.1", "--host", "-h", help="Bind socket to this host"
    ),
    port: int = typer.Option(8000, "--port", "-p", help="Bind socket to this port"),
    reload: bool = typer.Option(
        True, "--reload/--no-reload", help="Enable/disable auto-reload"
    ),
    vite: bool = typer.Option(
        True,
        "--vite/--no-vite",
        help="Start concurrent Vite dev server if package.json exists",
    ),
):
    """Start the development server (with concurrent Vite dev server if package.json exists)."""
    cwd = Path.cwd()
    cwd_str = str(cwd)
    if cwd_str not in sys.path:
        sys.path.insert(0, cwd_str)

    # If full-stack (package.json present) and vite is enabled, orchestrate Vite concurrently
    package_json = cwd / "package.json"
    vite_proc = None

    if package_json.exists() and vite:
        typer.secho(
            "⚡ Full-stack project detected. Starting Vite dev server...",
            fg=typer.colors.MAGENTA,
        )
        try:
            vite_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=cwd_str,
                stdout=sys.stdout,
                stderr=sys.stderr,
                shell=sys.platform == "win32",
            )
        except (OSError, subprocess.SubprocessError) as err:
            typer.secho(
                f"⚠️ Could not start Vite dev server: {err}",
                fg=typer.colors.YELLOW,
            )

    typer.secho(
        f"🚀 Astris entering orbit on http://{host}:{port}", fg=typer.colors.CYAN
    )

    try:
        reload_dirs = []
        if (cwd / "app").exists():
            reload_dirs.append(str(cwd / "app"))
        if (cwd / "database").exists():
            reload_dirs.append(str(cwd / "database"))
        if not reload_dirs:
            reload_dirs = [cwd_str]

        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=reload_dirs if reload else None,
            reload_includes=["*.py", ".env*"] if reload else None,
            reload_excludes=[
                "node_modules",
                "resources",
                "public",
                ".vite",
                ".git",
                "dist",
                "build",
            ]
            if reload
            else None,
            app_dir=cwd_str,
        )
    finally:
        if vite_proc:
            try:
                vite_proc.terminate()
                vite_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                vite_proc.kill()
            except OSError:
                pass


@orbit_cli.command("make:module")
def make_module(name: str):
    """Scaffold a full domain module (e.g. 'orbit make:module billing')."""
    clean_name = name.removesuffix("Module").lower()
    module_dir = Path.cwd() / "app" / "modules" / clean_name

    if module_dir.exists():
        typer.secho(
            f"Error: Module '{clean_name}' already exists!", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "__init__.py").touch()

    # 1. Controller stub
    controller_file = module_dir / f"{clean_name}_controller.py"
    controller_stub = f'''from astris.routing import Controller

controller = Controller(prefix="/{clean_name}s", tags=["{clean_name.capitalize()}"])


@controller.get("/")
async def list_{clean_name}s():
    return {{"message": "Hello from {clean_name} module!"}}
'''
    controller_file.write_text(controller_stub, encoding="utf-8")

    # 2. Service stub (docstring is sufficient, no redundant pass)
    service_file = module_dir / f"{clean_name}_service.py"
    service_stub = f'''class {clean_name.capitalize()}Service:
    """Business logic for {clean_name} domain."""
'''
    service_file.write_text(service_stub, encoding="utf-8")

    # 3. Model stub (SQLModel Table + DTOs)
    model_file = module_dir / f"{clean_name}_model.py"
    class_name = clean_name.capitalize()
    model_stub = f"""from astris.database import Field, SQLModel


class {class_name}Base(SQLModel):
    name: str = Field(index=True)


class {class_name}({class_name}Base, table=True):
    id: int | None = Field(default=None, primary_key=True)


class {class_name}Create({class_name}Base):
    pass


class {class_name}Public({class_name}Base):
    id: int
"""
    model_file.write_text(model_stub, encoding="utf-8")

    typer.secho(
        f"✓ Created module 'app/modules/{clean_name}' with controller, service, and model",
        fg=typer.colors.GREEN,
    )


@orbit_cli.command("make:controller")
def make_controller(
    name: str,
    module: str = typer.Option(
        None, "--module", "-m", help="Target module name (defaults to controller name)"
    ),
):
    """Scaffold a controller inside a domain module."""
    clean_name = name.removesuffix("Controller").lower()
    target_module = (module or clean_name).lower()
    module_dir = Path.cwd() / "app" / "modules" / target_module
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "__init__.py").touch()

    file_name = f"{clean_name}_controller.py"
    target_file = module_dir / file_name

    if target_file.exists():
        typer.secho(
            f"Error: {file_name} already exists in app/modules/{target_module}!",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    stub = f'''from astris.routing import Controller

controller = Controller(prefix="/{clean_name}s", tags=["{clean_name.capitalize()}"])


@controller.get("/")
async def list_{clean_name}s():
    return {{"message": "Hello from {clean_name}!"}}
'''
    target_file.write_text(stub, encoding="utf-8")
    typer.secho(
        f"✓ Created app/modules/{target_module}/{file_name}",
        fg=typer.colors.GREEN,
    )


@orbit_cli.command("make:model")
def make_model(
    name: str,
    module: str = typer.Option(
        None, "--module", "-m", help="Target module name (defaults to model name)"
    ),
):
    """Scaffold a SQLModel table model inside a domain module."""
    clean_name = name.removesuffix("Model").lower()
    class_name = name.removesuffix("Model").capitalize()
    target_module = (module or clean_name).lower()
    module_dir = Path.cwd() / "app" / "modules" / target_module
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "__init__.py").touch()

    file_name = f"{clean_name}_model.py"
    target_file = module_dir / file_name

    if target_file.exists():
        typer.secho(
            f"Error: {file_name} already exists in app/modules/{target_module}!",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    stub = f"""from astris.database import Field, SQLModel


class {class_name}Base(SQLModel):
    name: str = Field(index=True)


class {class_name}({class_name}Base, table=True):
    id: int | None = Field(default=None, primary_key=True)


class {class_name}Create({class_name}Base):
    pass


class {class_name}Public({class_name}Base):
    id: int
"""
    target_file.write_text(stub, encoding="utf-8")
    typer.secho(
        f"✓ Created app/modules/{target_module}/{file_name}",
        fg=typer.colors.GREEN,
    )


@orbit_cli.command("make:migration")
def make_migration(
    name: str,
    autogenerate: bool = typer.Option(
        True,
        "--autogenerate/--empty",
        help="Autogenerate schema diff from SQLModel models",
    ),
):
    """Generate a new versioned migration script."""
    from astris.database.migrations import create_migration

    try:
        create_migration(message=name, autogenerate=autogenerate)
        typer.secho(
            f"✓ Migration '{name}' generated successfully!",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error generating migration: {e}", fg=typer.colors.RED)
        raise typer.Exit(1) from e


@orbit_cli.command("migrate")
def migrate(
    revision: str = typer.Option(
        "head", "--revision", "-r", help="Target revision (default: head)"
    ),
):
    """Run pending database migrations."""
    from astris.database.migrations import run_migrations

    try:
        run_migrations(revision=revision)
        typer.secho(
            f"✓ Database migrated successfully to '{revision}'!",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error executing migrations: {e}", fg=typer.colors.RED)
        raise typer.Exit(1) from e


@orbit_cli.command("migrate:rollback")
def migrate_rollback(
    steps: int = typer.Option(
        1, "--steps", "-s", help="Number of migrations to roll back"
    ),
):
    """Roll back database migrations by N steps."""
    from astris.database.migrations import rollback_migrations

    try:
        target_revision = f"-{steps}"
        rollback_migrations(revision=target_revision)
        typer.secho(
            f"✓ Rolled back {steps} migration(s) successfully!",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error rolling back migrations: {e}", fg=typer.colors.RED)
        raise typer.Exit(1) from e


@orbit_cli.command("migrate:status")
def migrate_status():
    """Display current database migration revision and head status."""
    from astris.database.migrations import get_migration_status

    try:
        status = get_migration_status()
        current = status["current_revisions"] or ["None"]
        heads = status["heads"] or ["None"]
        up_to_date = status["is_up_to_date"]

        typer.secho(f"Current revision: {', '.join(current)}", fg=typer.colors.CYAN)
        typer.secho(f"Latest head:      {', '.join(heads)}", fg=typer.colors.CYAN)
        if up_to_date:
            typer.secho("✓ Database is up to date!", fg=typer.colors.GREEN)
        else:
            typer.secho(
                "⚠ Pending migrations exist! Run 'orbit migrate' to apply.",
                fg=typer.colors.YELLOW,
            )
    except Exception as e:
        typer.secho(f"Error checking migration status: {e}", fg=typer.colors.RED)
        raise typer.Exit(1) from e


@orbit_cli.command("key:generate")
def key_generate(
    show: bool = typer.Option(
        False, "--show", help="Display the generated key instead of writing to .env"
    ),
):
    """Generate and set the application encryption key (APP_KEY)."""
    import secrets

    key = secrets.token_urlsafe(32)
    if show:
        typer.secho(f"APP_KEY={key}", fg=typer.colors.CYAN)
        return

    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        env_path.write_text(f"APP_KEY={key}\n", encoding="utf-8")
        typer.secho("✓ Created .env and set APP_KEY", fg=typer.colors.GREEN)
        return

    content = env_path.read_text(encoding="utf-8")
    if "APP_KEY=" in content:
        lines = []
        replaced = False
        for line in content.splitlines():
            if line.startswith("APP_KEY="):
                lines.append(f"APP_KEY={key}")
                replaced = True
            else:
                lines.append(line)
        if not replaced:
            lines.append(f"APP_KEY={key}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        env_path.write_text(content.rstrip() + f"\nAPP_KEY={key}\n", encoding="utf-8")

    typer.secho("✓ Application key [APP_KEY] set successfully.", fg=typer.colors.GREEN)


@orbit_cli.command("make:auth")
def make_auth():
    """Scaffold complete authentication (routes, controller, service, model, and Inertia Vue pages)."""
    from astris.auth.installer import install_auth_starter

    try:
        install_auth_starter()
        typer.secho(
            "✓ Authentication scaffolding generated successfully!\n"
            "  - Backend:  app/modules/auth (controller, service, model)\n"
            "  - Frontend: resources/js/Pages/Auth (Login.vue, Register.vue)\n"
            "  - Frontend: resources/js/Pages/Dashboard.vue\n\n"
            "Next steps:\n"
            '  1. Run: uv run orbit make:migration "create_users_table"\n'
            "  2. Run: uv run orbit migrate",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error generating auth scaffolding: {e}", fg=typer.colors.RED)
        raise typer.Exit(1) from e
