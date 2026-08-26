import json
from typing import Any
from urllib.parse import quote

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.responses import JSONResponse, RedirectResponse, Response


def format_validation_errors(
    exc: RequestValidationError | ValidationError,
) -> dict[str, str]:
    """Extract a clean, human-readable dictionary of field -> message from Pydantic validation errors."""
    errors: dict[str, str] = {}
    for error in exc.errors():
        # Strip internal FastAPI/Pydantic location qualifiers like 'body', 'query', '__root__'
        raw_loc = error.get("loc")
        loc_parts: list[str] = []
        if isinstance(raw_loc, (tuple, list)):
            for part in raw_loc:
                part_str = f"{part}"
                if part_str not in (
                    "body",
                    "query",
                    "header",
                    "cookie",
                    "path",
                    "__root__",
                ):
                    loc_parts.append(part_str)

        field = ".".join(loc_parts) if loc_parts else "non_field_errors"
        if field not in errors:
            msg = error.get("msg")
            errors[field] = msg if isinstance(msg, str) else "Invalid value"
    return errors


def create_inertia_validation_response(
    request: Request,
    errors: dict[str, Any],
) -> Response:
    """Create an Inertia-compliant validation error response.

    Returns a 303 redirect with flashed errors for state-changing form requests,
    or a 422 JSON response with the X-Inertia header.
    """
    referer = request.headers.get("Referer")
    if referer and request.method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        if hasattr(request, "session"):
            request.session["_errors"] = errors
        response = RedirectResponse(url=referer, status_code=303)
        response.set_cookie(
            key="_inertia_errors",
            value=quote(json.dumps(errors)),
            path="/",
            httponly=True,
            samesite="lax",
            max_age=10,
        )
        return response

    return JSONResponse(
        status_code=422,
        content={"errors": errors},
        headers={"X-Inertia": "true"},
    )


async def inertia_validation_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:
    """Handle validation errors for Inertia requests by returning an Inertia-compliant

    303 redirect with session errors, or a standard 422 JSON response for API consumers.
    """
    if isinstance(exc, (RequestValidationError, ValidationError)):
        errors = format_validation_errors(exc)
        detail = exc.errors()
    else:
        errors = {"non_field_errors": "Validation error"}
        detail = [{"msg": "Validation error", "type": "value_error"}]

    is_inertia = request.headers.get("X-Inertia") == "true"

    if is_inertia:
        return create_inertia_validation_response(request, errors)

    return JSONResponse(
        status_code=422,
        content={"detail": detail, "errors": errors},
    )


async def inertia_http_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:
    """Handle HTTPExceptions for Inertia and standard API requests.

    Formats 422 unprocessable entity errors as Inertia-compliant 303 redirects or {"errors": {...}}
    responses with the X-Inertia header, so frontend form validation states update seamlessly.
    """
    is_inertia = request.headers.get("X-Inertia") == "true"
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "An error occurred")

    if is_inertia and status_code == 422:
        if isinstance(detail, dict):
            errors = {str(k): str(v) for k, v in detail.items()}
        elif isinstance(detail, list):
            errors = {}
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc", ["non_field_errors"])[-1]
                    errors[str(loc)] = str(item.get("msg", "Invalid value"))
                else:
                    errors["non_field_errors"] = str(item)
        elif isinstance(detail, str):
            errors = {"non_field_errors": detail}
        else:
            errors = {"non_field_errors": "Validation error"}

        return create_inertia_validation_response(request, errors)

    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers,
    )
