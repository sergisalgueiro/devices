from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic_extra_types.country import CountryAlpha2
from pydantic_extra_types.language_code import LanguageAlpha2
from pydantic_extra_types.timezone_name import TimeZoneName


class CustomerCreate(BaseModel):
    """Schema for creating a customer."""

    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: EmailStr = Field(..., description="Valid customer email address")
    language: LanguageAlpha2 | None = Field(
        default=None,
        description="ISO 639-1 2-letter language code (e.g., 'en', 'es', 'de')",
    )
    country: CountryAlpha2 | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 2-letter country code (e.g., 'ES', 'US')",
    )
    timezone: TimeZoneName | None = Field(
        default=None,
        description="IANA Time Zone identifier (e.g., 'Europe/Madrid', 'UTC')",
    )


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer."""

    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Customer name"
    )
    email: EmailStr | None = Field(
        default=None, description="Valid customer email address"
    )
    language: LanguageAlpha2 | None = Field(
        default=None,
        description="ISO 639-1 2-letter language code (e.g., 'en', 'es', 'de')",
    )
    country: CountryAlpha2 | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 2-letter country code (e.g., 'ES', 'US')",
    )
    timezone: TimeZoneName | None = Field(
        default=None,
        description="IANA Time Zone identifier (e.g., 'Europe/Madrid', 'UTC')",
    )


class CustomerResponse(BaseModel):
    """Schema for customer response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    language: str | None = None
    country: str | None = None
    timezone: str | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def unwrap_value_objects(cls, data: Any) -> Any:
        """Unwrap Value Objects when validating from domain entity objects."""
        if hasattr(data, "__dataclass_fields__"):
            return {
                field_name: getattr(field_val, "value", field_val)
                for field_name, field_val in (
                    (f, getattr(data, f)) for f in data.__dataclass_fields__
                )
            }
        return data


class PaginatedCustomersResponse(BaseModel):
    """Paginated list of customers."""

    items: list[CustomerResponse]
    next_cursor: str | None
    has_more: bool
