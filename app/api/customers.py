from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import EmailStr
from starlette import status

from app.api.dependencies import (
    CreateCustomerHandlerDep,
    DbSessionDep,
    GetCustomerHandlerDep,
    ListCustomersHandlerDep,
)
from app.application.customer.create_customer import CreateCustomerCommand
from app.application.customer.get_customer import GetCustomerQuery
from app.application.customer.list_customers import ListCustomersQuery
from app.schemas.customer import CustomerCreate, CustomerResponse, PaginatedCustomersResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a customer")
async def create_customer(
    payload: CustomerCreate,
    db: DbSessionDep,
    handler: CreateCustomerHandlerDep,
) -> CustomerResponse:
    """
    Register a new customer.

    - Returns **201 Created** with the created customer.
    - Returns **409 Conflict** if the email is already registered.
    - Returns **422 Unprocessable Entity** if validation fails.
    """
    async with db.begin():
        customer = await handler.handle(
            CreateCustomerCommand(
                name=payload.name,
                email=str(payload.email),
                language=str(payload.language) if payload.language is not None else None,
                country=str(payload.country) if payload.country is not None else None,
                timezone=str(payload.timezone) if payload.timezone is not None else None,
            )
        )
    return CustomerResponse.model_validate(customer)


@router.get("", summary="List customers")
async def list_customers(
    handler: ListCustomersHandlerDep,
    email: Annotated[EmailStr | None, Query(description="Filter by exact email address")] = None,
    country: Annotated[str | None, Query(description="Filter by ISO 3166-1 alpha-2 country code")] = None,
    language: Annotated[str | None, Query(description="Filter by ISO 639-1 language code")] = None,
    name: Annotated[str | None, Query(description="Filter by partial name match (case-insensitive)")] = None,
    sort_by: Annotated[str, Query(pattern="^(created_at|name|email)$", description="Field to sort by")] = "created_at",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$", description="Sort direction")] = "asc",
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum results per page")] = 20,
    cursor: Annotated[str | None, Query(description="Opaque pagination cursor from previous response")] = None,
) -> PaginatedCustomersResponse:
    """
    List customers with optional filters and cursor-based pagination.

    - Returns **200** with a paginated list of customers and a cursor for the next page.
    - Filters combine with AND logic.
    - Returns **422** if filter values fail validation.
    """
    result = await handler.handle(
        ListCustomersQuery(
            email=str(email) if email is not None else None,
            country=country,
            language=language,
            name=name,
            sort_field=sort_by,
            sort_direction=sort_dir,
            limit=limit,
            cursor=cursor,
        )
    )
    return PaginatedCustomersResponse(
        items=[CustomerResponse.model_validate(c) for c in result.items],
        next_cursor=result.next_cursor,
        has_more=result.has_more,
    )


@router.get("/{customer_id}", summary="Get a customer")
async def get_customer(
    customer_id: UUID,
    handler: GetCustomerHandlerDep,
) -> CustomerResponse:
    """
    Retrieve a customer by ID.

    - Returns **404 Not Found** if the customer does not exist.
    """
    customer = await handler.handle(GetCustomerQuery(customer_id=customer_id))
    return CustomerResponse.model_validate(customer)
