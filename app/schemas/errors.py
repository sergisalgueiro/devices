"""
Reusable per-status-code response definitions for FastAPI route `responses=` parameters.

Usage:
    from app.schemas.errors import Err

    @router.post(
        "/items",
        responses={**Err.conflict, **Err.unprocessable},
    )
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error body schemas
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Body returned by all domain-level error handlers (404, 409, 500)."""

    detail: str = Field(description="Human-readable description of the error")


class ValidationErrorItem(BaseModel):
    """A single Pydantic / FastAPI validation failure."""

    loc: list[str | int] = Field(
        description="Path to the failing field, e.g. ['body', 'email']"
    )
    msg: str = Field(description="Human-readable reason the validation failed")
    type: str = Field(description="Machine-readable error type identifier")
    input: Any = Field(default=None, description="The value that was rejected")
    ctx: dict[str, Any] | None = Field(default=None, description="Extra context from the validator")


class ValidationErrorResponse(BaseModel):
    """Body returned on 422 Unprocessable Content."""

    detail: list[ValidationErrorItem]


# ---------------------------------------------------------------------------
# Per-status response dicts — pass these directly in route `responses=`
# ---------------------------------------------------------------------------


class Err:
    """
    Namespace of ready-made response dicts for common HTTP error codes.

    Spread one or more into the `responses=` kwarg of any route:

        @router.get("/items/{id}", responses={**Err.not_found})
        @router.post("/items",    responses={**Err.conflict, **Err.unprocessable})
    """

    not_found: dict[int, dict[str, Any]] = {
        404: {
            "model": ErrorDetail,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Resource with the given id was not found"}
                }
            },
        }
    }

    conflict: dict[int, dict[str, Any]] = {
        409: {
            "model": ErrorDetail,
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "A resource with the same unique value already exists"}
                }
            },
        }
    }

    unprocessable: dict[int, dict[str, Any]] = {
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address: The email address is not valid. It must have exactly one @-sign.",
                                "type": "value_error",
                                "input": "invalid-email",
                            }
                        ]
                    }
                }
            },
        }
    }

    internal: dict[int, dict[str, Any]] = {
        500: {
            "model": ErrorDetail,
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Internal server error"}
                }
            },
        }
    }
