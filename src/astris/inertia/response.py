import html
import json
from pathlib import Path
from typing import Any

from fastapi import Request, Response
from starlette.responses import HTMLResponse, JSONResponse
from starlette.types import Receive, Scope, Send

from astris.inertia.shared import resolve_shared_props
from astris.inertia.vite import get_vite_tags


class InertiaResponse(Response):
    """Inertia response handler returning JSON on dynamic visits and HTML on initial load."""

    def __init__(
        self,
        request: Request,
        component: str,
        props: dict[str, Any] | None = None,
        root_template: str = "resources/views/root.html",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.request = request
        self.component = component
        self.props = props or {}
        self.root_template = root_template
        self.status_code = status_code
        self._custom_headers = headers or {}
        super().__init__(status_code=status_code)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        is_inertia = self.request.headers.get("X-Inertia") == "true"

        shared_props = await resolve_shared_props(self.request)
        merged_props = {**shared_props, **self.props}

        page_data = {
            "component": self.component,
            "props": merged_props,
            "url": str(self.request.url.path),
            "version": "",
        }

        if is_inertia:
            response: Response = JSONResponse(
                content=page_data,
                status_code=self.status_code,
                headers={
                    "X-Inertia": "true",
                    "Vary": "X-Inertia",
                    **self._custom_headers,
                },
            )
        else:
            template_path = Path.cwd() / self.root_template
            vite_tags = get_vite_tags(base_path=Path.cwd())

            if not template_path.exists():
                content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Astris App</title>
</head>
<body>
    <div id="app" data-page="{html.escape(json.dumps(page_data))}"></div>
    {vite_tags}
</body>
</html>"""
            else:
                raw_html = template_path.read_text(encoding="utf-8")
                escaped_page = html.escape(json.dumps(page_data))
                content = raw_html.replace(
                    "@inertia", f'<div id="app" data-page="{escaped_page}"></div>'
                )
                if "@vite" in content:
                    content = content.replace("@vite", vite_tags)

            response = HTMLResponse(
                content=content,
                status_code=self.status_code,
                headers=self._custom_headers,
            )

        if self.request.cookies.get("_inertia_flash"):
            response.delete_cookie(key="_inertia_flash", path="/")
        if self.request.cookies.get("_inertia_errors"):
            response.delete_cookie(key="_inertia_errors", path="/")

        await response(scope, receive, send)
