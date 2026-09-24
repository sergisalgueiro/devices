from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.domain.device import Device
from app.domain.exceptions import (
    InvalidCustomerIdError,
    InvalidDeviceIdError,
    InvalidDeviceStatusError,
    InvalidSerialNumberError,
    InvalidTimeZoneError,
    InvalidUpdatedAtError,
)
from app.domain.value_objects import (
    CreatedAt,
    CustomerId,
    DeviceId,
    DeviceStatus,
    DeviceStatusEnum,
    SerialNumber,
    TimeZone,
    UpdatedAt,
)


class TestDeviceId:
    def test_valid_default_uuid(self):
        vo = DeviceId()
        assert isinstance(vo.value, UUID)

    def test_valid_explicit_uuid(self):
        raw_uuid = uuid4()
        vo = DeviceId(raw_uuid)
        assert vo.value == raw_uuid

    def test_valid_string_uuid_parsed(self):
        raw_uuid = uuid4()
        vo = DeviceId(str(raw_uuid))
        assert vo.value == raw_uuid

    def test_invalid_uuid_string(self):
        with pytest.raises(InvalidDeviceIdError):
            DeviceId("invalid-uuid-format")

    def test_invalid_type(self):
        with pytest.raises(InvalidDeviceIdError):
            DeviceId(12345)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = DeviceId()
        with pytest.raises(FrozenInstanceError):
            vo.value = uuid4()  # type: ignore[misc]

    def test_equality_by_value(self):
        raw_uuid = uuid4()
        vo1 = DeviceId(raw_uuid)
        vo2 = DeviceId(raw_uuid)
        vo3 = DeviceId(uuid4())
        assert vo1 == vo2
        assert vo1 != vo3

    def test_primitive_accessor(self):
        raw_uuid = uuid4()
        vo = DeviceId(raw_uuid)
        assert vo.value == raw_uuid
        assert str(vo) == str(raw_uuid)


class TestSerialNumber:
    def test_valid_serial_numbers(self):
        for sn in ["SN-00123456", "DEV_99", "MAC:00:11:22:33:44:55", "DEVICE.V1.2"]:
            vo = SerialNumber(sn)
            assert vo.value == sn

    def test_trimming_whitespace(self):
        vo = SerialNumber("  SN-998877  ")
        assert vo.value == "SN-998877"

    def test_invalid_empty_or_whitespace(self):
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber("")
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber("   ")

    def test_invalid_length_exceeded(self):
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber("A" * 101)

    def test_invalid_characters(self):
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber("SN 12345")  # contains space
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber("SN@12345")  # contains @

    def test_invalid_type(self):
        with pytest.raises(InvalidSerialNumberError):
            SerialNumber(12345)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = SerialNumber("SN-12345")
        with pytest.raises(FrozenInstanceError):
            vo.value = "SN-67890"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert SerialNumber("SN-1") == SerialNumber("SN-1")
        assert SerialNumber("SN-1") != SerialNumber("SN-2")

    def test_primitive_accessor(self):
        vo = SerialNumber("SN-1")
        assert vo.value == "SN-1"
        assert str(vo) == "SN-1"


class TestDeviceStatus:
    def test_default_status_is_offline(self):
        vo = DeviceStatus()
        assert vo.value == DeviceStatusEnum.OFFLINE.value
        assert vo.is_offline is True
        assert vo.is_online is False
        assert vo.is_connected is False

    def test_valid_statuses_from_enum(self):
        for status_enum in DeviceStatusEnum:
            vo = DeviceStatus(status_enum)
            assert vo.value == status_enum.value

    def test_valid_statuses_from_string_case_insensitive(self):
        assert DeviceStatus("online").value == "online"
        assert DeviceStatus("ONLINE").value == "online"
        assert DeviceStatus("  OffLine  ").value == "offline"
        assert DeviceStatus("provisioning").value == "provisioning"
        assert DeviceStatus("maintenance").value == "maintenance"
        assert DeviceStatus("error").value == "error"
        assert DeviceStatus("decommissioned").value == "decommissioned"

    def test_factory_methods(self):
        assert DeviceStatus.online().value == "online"
        assert DeviceStatus.online().is_online is True
        assert DeviceStatus.online().is_connected is True

        assert DeviceStatus.offline().value == "offline"
        assert DeviceStatus.offline().is_offline is True

        assert DeviceStatus.provisioning().value == "provisioning"
        assert DeviceStatus.maintenance().value == "maintenance"
        assert DeviceStatus.error().value == "error"
        assert DeviceStatus.decommissioned().value == "decommissioned"

    def test_invalid_status_string(self):
        with pytest.raises(InvalidDeviceStatusError):
            DeviceStatus("unknown_status")

    def test_invalid_type(self):
        with pytest.raises(InvalidDeviceStatusError):
            DeviceStatus(123)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = DeviceStatus.online()
        with pytest.raises(FrozenInstanceError):
            vo.value = "offline"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert DeviceStatus.online() == DeviceStatus("online")
        assert DeviceStatus.online() != DeviceStatus.offline()

    def test_primitive_accessor(self):
        vo = DeviceStatus.online()
        assert vo.value == "online"
        assert str(vo) == "online"


class TestUpdatedAt:
    def test_valid_default_utc(self):
        vo = UpdatedAt()
        assert isinstance(vo.value, datetime)
        assert vo.value.tzinfo == timezone.utc

    def test_valid_explicit_utc(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        vo = UpdatedAt(dt)
        assert vo.value == dt

    def test_invalid_naive_datetime(self):
        naive_dt = datetime(2026, 1, 1, 12, 0, 0)
        with pytest.raises(InvalidUpdatedAtError):
            UpdatedAt(naive_dt)

    def test_invalid_non_utc_timezone(self):
        madrid_tz = ZoneInfo("Europe/Madrid")
        madrid_dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=madrid_tz)
        with pytest.raises(InvalidUpdatedAtError):
            UpdatedAt(madrid_dt)

    def test_invalid_type(self):
        with pytest.raises(InvalidUpdatedAtError):
            UpdatedAt("2026-01-01T00:00:00Z")  # type: ignore[arg-type]

    def test_immutability(self):
        vo = UpdatedAt()
        with pytest.raises(FrozenInstanceError):
            vo.value = datetime.now(timezone.utc)  # type: ignore[misc]

    def test_equality_by_value(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert UpdatedAt(dt) == UpdatedAt(dt)

    def test_primitive_accessor(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        vo = UpdatedAt(dt)
        assert vo.value == dt


class TestDeviceEntity:
    def test_create_device_with_vos(self):
        device_id = DeviceId()
        customer_id = CustomerId()
        created_at = CreatedAt()
        updated_at = UpdatedAt()
        timezone_vo = TimeZone("Europe/Madrid")

        device = Device(
            id=device_id,
            serial_number=SerialNumber("SN-IOT-001"),
            customer_id=customer_id,
            status=DeviceStatus.online(),
            timezone=timezone_vo,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert device.id == device_id
        assert device.serial_number == SerialNumber("SN-IOT-001")
        assert device.customer_id == customer_id
        assert device.status == DeviceStatus.online()
        assert device.timezone == timezone_vo
        assert device.created_at == created_at
        assert device.updated_at == updated_at

        # Test value accessors
        assert device.id.value == device_id.value
        assert device.serial_number.value == "SN-IOT-001"
        assert device.customer_id.value == customer_id.value
        assert device.status.value == "online"
        assert device.timezone is not None and device.timezone.value == "Europe/Madrid"
        assert device.created_at.value == created_at.value
        assert device.updated_at.value == updated_at.value

    def test_create_device_with_defaults(self):
        customer_id = CustomerId()
        device = Device(
            serial_number=SerialNumber("SN-IOT-002"),
            customer_id=customer_id,
        )

        assert isinstance(device.id, DeviceId)
        assert isinstance(device.id.value, UUID)
        assert device.serial_number == SerialNumber("SN-IOT-002")
        assert device.customer_id == customer_id
        assert device.status == DeviceStatus.offline()
        assert device.timezone is None
        assert isinstance(device.created_at, CreatedAt)
        assert device.created_at.value.tzinfo == timezone.utc
        assert isinstance(device.updated_at, UpdatedAt)
        assert device.updated_at.value.tzinfo == timezone.utc

    def test_set_timezone(self):
        device = Device(
            serial_number=SerialNumber("SN-100"),
            customer_id=CustomerId(),
        )
        assert device.timezone is None
        initial_updated_at = device.updated_at.value

        device.set_timezone(TimeZone("UTC"))
        assert device.timezone == TimeZone("UTC")
        assert device.timezone.value == "UTC"
        assert device.updated_at.value >= initial_updated_at

        utc_updated_at = device.updated_at.value
        device.set_timezone(None)
        assert device.timezone is None
        assert device.updated_at.value >= utc_updated_at

    def test_connect_and_disconnect(self):
        device = Device(
            serial_number=SerialNumber("SN-100"),
            customer_id=CustomerId(),
        )
        initial_updated_at = device.updated_at.value

        device.connect()
        assert device.status.is_online is True
        assert device.status.value == "online"
        assert device.updated_at.value >= initial_updated_at

        online_updated_at = device.updated_at.value
        device.disconnect()
        assert device.status.is_offline is True
        assert device.status.value == "offline"
        assert device.updated_at.value >= online_updated_at

    def test_decommission(self):
        device = Device(
            serial_number=SerialNumber("SN-100"),
            customer_id=CustomerId(),
        )
        device.decommission()
        assert device.status == DeviceStatus.decommissioned()
        assert device.status.value == "decommissioned"

    def test_reassign_customer(self):
        old_customer_id = CustomerId()
        new_customer_id = CustomerId()
        device = Device(
            serial_number=SerialNumber("SN-100"),
            customer_id=old_customer_id,
        )

        device.reassign_customer(new_customer_id)
        assert device.customer_id == new_customer_id

    def test_update_status(self):
        device = Device(
            serial_number=SerialNumber("SN-100"),
            customer_id=CustomerId(),
        )
        device.update_status(DeviceStatus.maintenance())
        assert device.status == DeviceStatus.maintenance()
        assert device.status.value == "maintenance"

        device.update_status(DeviceStatus.error())
        assert device.status == DeviceStatus.error()
        assert device.status.value == "error"
