import json
import socket
from pathlib import Path
from urllib.parse import urlparse


def is_vite_running(url: str = "http://localhost:5173", timeout: float = 0.05) -> bool:
    """Check if the Vite dev server is reachable."""
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5173
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, TimeoutError):
        return False


def get_vite_tags(
    entry: str = "resources/js/app.ts",
    base_path: Path | None = None,
    vite_dev_url: str = "http://localhost:5173",
) -> str:
    """Generate script and link tags by detecting active Vite dev server or parsing public/build/.vite/manifest.json."""
    base = base_path or Path.cwd()

    # 1. Check for hot file (e.g., public/hot) or active Vite dev server
    hot_file = base / "public" / "hot"
    dev_url = vite_dev_url
    if hot_file.exists():
        dev_url = hot_file.read_text(encoding="utf-8").strip()

    if is_vite_running(dev_url):
        clean_url = dev_url.rstrip("/")
        clean_entry = entry.lstrip("/")
        return (
            f"<!-- Vite Dev Server Scripts -->\n"
            f'<script type="module" src="{clean_url}/@vite/client"></script>\n'
            f'<script type="module" src="{clean_url}/{clean_entry}"></script>'
        )

    # 2. Parse production manifest from public/build/.vite/manifest.json or public/build/manifest.json
    manifest_paths = [
        base / "public" / "build" / ".vite" / "manifest.json",
        base / "public" / "build" / "manifest.json",
    ]

    manifest_data: dict[str, dict] | None = None
    for manifest_path in manifest_paths:
        if manifest_path.exists():
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                continue

    if manifest_data:
        clean_entry = entry.lstrip("/")
        entry_info = manifest_data.get(clean_entry)
        if not entry_info:
            for key, val in manifest_data.items():
                if key.endswith(clean_entry) or val.get("src") == clean_entry:
                    entry_info = val
                    break

        if entry_info:
            tags = ["<!-- Production Vite Assets -->"]
            # CSS links
            for css_file in entry_info.get("css", []):
                tags.append(
                    f'<link rel="stylesheet" href="/build/{css_file.lstrip("/")}">'
                )
            # JS script
            js_file = entry_info.get("file", "")
            if js_file:
                tags.append(
                    f'<script type="module" src="/build/{js_file.lstrip("/")}"></script>'
                )

            return "\n".join(tags)

    # 3. Fallback if neither active dev server nor manifest is found
    clean_url = vite_dev_url.rstrip("/")
    clean_entry = entry.lstrip("/")
    return (
        f"<!-- Vite Assets (Fallback) -->\n"
        f'<script type="module" src="{clean_url}/@vite/client"></script>\n'
        f'<script type="module" src="{clean_url}/{clean_entry}"></script>'
    )
