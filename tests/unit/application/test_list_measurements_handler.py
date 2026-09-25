from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.measurement.list_measurements import ListMeasurementsHandler, ListMeasurementsQuery
from app.domain.exceptions import DeviceNotFoundError
from app.domain.repositories import MeasurementListFilters, PaginatedResult


class TestListMeasurementsHandler:
    async def test_device_not_found_raises_error(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = None
        measurement_repo = AsyncMock()

        handler = ListMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        with pytest.raises(DeviceNotFoundError):
            await handler.handle(ListMeasurementsQuery(device_id=uuid4()))

        measurement_repo.list.assert_not_awaited()

    async def test_delegates_with_correct_filters(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = object()
        measurement_repo = AsyncMock()
        measurement_repo.list.return_value = PaginatedResult(items=[], next_cursor=None, has_more=False)

        device_id = uuid4()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 2, tzinfo=timezone.utc)

        handler = ListMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        await handler.handle(
            ListMeasurementsQuery(
                device_id=device_id,
                type="temperature",
                start_time=start,
                end_time=end,
                limit=10,
            )
        )

        measurement_repo.list.assert_awaited_once_with(
            device_id=device_id,
            filters=MeasurementListFilters(type="temperature", start_time=start, end_time=end),
            sort_field="timestamp",
            sort_direction="desc",
            limit=10,
            cursor=None,
        )

    async def test_passes_sort_and_pagination_params(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = object()
        measurement_repo = AsyncMock()
        measurement_repo.list.return_value = PaginatedResult(items=[], next_cursor=None, has_more=False)

        device_id = uuid4()
        handler = ListMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        await handler.handle(
            ListMeasurementsQuery(
                device_id=device_id,
                sort_direction="asc",
                limit=5,
                cursor="some-cursor",
            )
        )

        measurement_repo.list.assert_awaited_once_with(
            device_id=device_id,
            filters=MeasurementListFilters(),
            sort_field="timestamp",
            sort_direction="asc",
            limit=5,
            cursor="some-cursor",
        )

    async def test_returns_paginated_result_with_has_more(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = object()
        measurement_repo = AsyncMock()
        expected = PaginatedResult(items=[], next_cursor="cursor-abc", has_more=True)
        measurement_repo.list.return_value = expected

        handler = ListMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        result = await handler.handle(ListMeasurementsQuery(device_id=uuid4(), limit=5))

        assert result is expected
        assert result.has_more is True
        assert result.next_cursor == "cursor-abc"
