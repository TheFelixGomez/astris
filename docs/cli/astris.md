# Astris Project Generator

The `astris` CLI is the project scaffolding tool used to create new Astris applications.

## Usage

### 1. One-off Execution (No install required)
```bash
uvx --from astris-python astris new <project_name> [options]
```

### 2. Global Installation
Install the CLI globally on your system using `uv tool` or `pipx`:

```bash
uv tool install astris-python
# Or: pipx install astris-python
```

Once installed, invoke the generator directly from anywhere:

```bash
astris new <project_name> [options]
```

## Options & Flags

| Flag | Type | Description |
| :--- | :--- | :--- |
| `--auth / --no-auth` | boolean | Enable or disable the full-stack authentication starter kit (default: enabled) |
| `--claude` | boolean | Scaffold Claude Code agent skills in `.claude/skills` alongside universal `.agents/skills` |
| `--local <path>` | string | Links a local clone of the Astris framework instead of PyPI (for framework contributors) |

## Examples

### Create a standard application (with Auth included):
```bash
uvx --from astris-python astris new saas_app
```

### Create a minimal application without authentication:
```bash
uvx --from astris-python astris new api_only_app --no-auth
```

## Next Steps

* Deploying your project: [Production & Docker](/deployment/production).
