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
    stack = list(getattr(app, "routes", []))

    while stack:
        route = stack.pop()
        if getattr(route, "path", None) == path:
            return True
        for cand in getattr(route, "_effective_candidates", []):
            if getattr(cand, "path", None) == path:
                return True
        orig = getattr(route, "original_router", None)
        if orig and hasattr(orig, "routes"):
            stack.extend(orig.routes)
        if hasattr(route, "routes"):
            stack.extend(route.routes)

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
