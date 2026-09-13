from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    Path,
    Query,
    Security,
    UploadFile,
    status,
)

# Alias to avoid name collisions with standard library pathlib.Path
PathParam = Path


class Controller(APIRouter):
    """Core Astris Controller router."""


def has_route(target: Any, path: str) -> bool:
    """Check if a route path is registered in the application or request router tree."""
    app = getattr(target, "app", target)
    routes = getattr(app, "routes", [])
    for route in routes:
        if getattr(route, "path", None) == path:
            return True
        for sub in getattr(getattr(route, "original_router", None), "routes", []):
            if getattr(sub, "path", None) == path:
                return True
        for sub in getattr(route, "routes", []):
            if getattr(sub, "path", None) == path:
                return True
    return False


__all__ = [
    "Body",
    "Controller",
    "Cookie",
    "Depends",
    "File",
    "Form",
    "Header",
    "Path",
    "PathParam",
    "Query",
    "Security",
    "UploadFile",
    "has_route",
    "status",
]
