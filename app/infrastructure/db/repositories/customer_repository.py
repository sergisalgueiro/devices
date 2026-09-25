from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.customer import Customer
from app.domain.repositories import CustomerListFilters, CustomerRepository, PaginatedResult
from app.domain.value_objects import Country, CreatedAt, CustomerId, Email, Language, Name, TimeZone
from app.infrastructure.db.models.customer import CustomerModel

logger = logging.getLogger(__name__)

_SORT_COLUMNS: dict[str, Any] = {
    "created_at": CustomerModel.created_at,
    "name": CustomerModel.name,
    "email": CustomerModel.email,
}


def _encode_cursor(sort_field: str, sort_direction: str, sort_value: Any, row_id: UUID) -> str:
    v = sort_value.isoformat() if isinstance(sort_value, datetime) else str(sort_value)
    payload = {"f": sort_field, "d": sort_direction, "v": v, "id": str(row_id)}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    return encoded.rstrip("=")


def _decode_cursor(cursor: str) -> tuple[str, str, Any, UUID]:
    padded = cursor + "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded).decode())
    sort_field: str = payload["f"]
    sort_direction: str = payload["d"]
    raw_v: str = payload["v"]
    sort_value: Any = datetime.fromisoformat(raw_v) if sort_field == "created_at" else raw_v
    return sort_field, sort_direction, sort_value, UUID(payload["id"])


class SqlAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of the CustomerRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        logger.debug("SELECT customer: id=%s", customer_id)
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.id == customer_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            logger.debug("Customer not found in DB: id=%s", customer_id)
            return None
        logger.debug("Customer found: id=%s", customer_id)
        return self._to_domain(row)

    async def get_by_email(self, email: str) -> Customer | None:
        logger.debug("SELECT customer: email=%s", email)
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def save(self, customer: Customer) -> None:
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.id == customer.id.value)
        )
        row = result.scalar_one_or_none()

        if row is None:
            logger.debug("INSERT customer: id=%s", customer.id.value)
            row = CustomerModel(id=customer.id.value)
            self._session.add(row)
        else:
            logger.debug("UPDATE customer: id=%s", customer.id.value)

        row.name = customer.name.value
        row.email = customer.email.value
        row.language = customer.language.value if customer.language is not None else None
        row.country = customer.country.value if customer.country is not None else None
        row.timezone = customer.timezone.value if customer.timezone is not None else None
        row.created_at = customer.created_at.value

        await self._session.flush()
        logger.debug("Customer flushed: id=%s", customer.id.value)

    async def list(
        self,
        filters: CustomerListFilters,
        sort_field: str,
        sort_direction: str,
        limit: int,
        cursor: str | None,
    ) -> PaginatedResult[Customer]:
        logger.debug(
            "LIST customers: sort=%s/%s, limit=%d, cursor=%s",
            sort_field, sort_direction, limit, cursor,
        )

        if cursor is not None:
            sort_field, sort_direction, cursor_sort_value, cursor_id = _decode_cursor(cursor)

        col = _SORT_COLUMNS[sort_field]
        stmt = select(CustomerModel)

        if filters.email is not None:
            stmt = stmt.where(CustomerModel.email == filters.email)
        if filters.country is not None:
            stmt = stmt.where(CustomerModel.country == filters.country)
        if filters.language is not None:
            stmt = stmt.where(CustomerModel.language == filters.language)
        if filters.name is not None:
            stmt = stmt.where(CustomerModel.name.ilike(f"%{filters.name}%"))

        if cursor is not None:
            if sort_direction == "asc":
                stmt = stmt.where(
                    or_(col > cursor_sort_value, and_(col == cursor_sort_value, CustomerModel.id > cursor_id))
                )
            else:
                stmt = stmt.where(
                    or_(col < cursor_sort_value, and_(col == cursor_sort_value, CustomerModel.id < cursor_id))
                )

        if sort_direction == "asc":
            stmt = stmt.order_by(col.asc(), CustomerModel.id.asc())
        else:
            stmt = stmt.order_by(col.desc(), CustomerModel.id.desc())

        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor: str | None = None
        if has_more and items:
            last = items[-1]
            next_cursor = _encode_cursor(sort_field, sort_direction, getattr(last, sort_field), last.id)

        return PaginatedResult(
            items=[self._to_domain(row) for row in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _to_domain(row: CustomerModel) -> Customer:
        return Customer(
            id=CustomerId(row.id),
            name=Name(row.name),
            email=Email(row.email),
            language=Language(row.language) if row.language is not None else None,
            country=Country(row.country) if row.country is not None else None,
            timezone=TimeZone(row.timezone) if row.timezone is not None else None,
            created_at=CreatedAt(row.created_at),
        )
