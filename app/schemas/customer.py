from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic_extra_types.country import CountryAlpha2
from pydantic_extra_types.language_code import LanguageAlpha2
from pydantic_extra_types.timezone_name import TimeZoneName

from app.schemas.base import DomainResponseBase


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


class CustomerResponse(DomainResponseBase):
    """Schema for customer response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique customer identifier")
    name: str = Field(description="Customer name")
    email: EmailStr = Field(description="Customer email address")
    language: str | None = Field(default=None, description="ISO 639-1 2-letter language code")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code")
    timezone: str | None = Field(default=None, description="IANA Time Zone identifier")
    created_at: datetime = Field(description="UTC timestamp when the customer was created")


class PaginatedCustomersResponse(BaseModel):
    """Paginated list of customers."""

    items: list[CustomerResponse] = Field(description="Customers on this page")
    next_cursor: str | None = Field(description="Opaque cursor to pass as `cursor` to retrieve the next page; null if no more pages")
    has_more: bool = Field(description="Whether additional pages exist")
