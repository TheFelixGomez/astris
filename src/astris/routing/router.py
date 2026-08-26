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
    "status",
]
