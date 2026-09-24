from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.customer import Customer
from app.domain.exceptions import (
    InvalidCountryError,
    InvalidCustomerIdError,
    InvalidEmailError,
    InvalidLanguageError,
    InvalidNameError,
    InvalidTimeZoneError,
    InvalidTimestampError,
)
from app.domain.value_objects import (
    Country,
    CreatedAt,
    CustomerId,
    Email,
    Language,
    Name,
    TimeZone,
)


class TestCustomerId:
    def test_valid_default_uuid(self):
        vo = CustomerId()
        assert isinstance(vo.value, UUID)
        assert isinstance(vo.value, UUID)

    def test_valid_explicit_uuid(self):
        raw_uuid = uuid4()
        vo = CustomerId(raw_uuid)
        assert vo.value == raw_uuid

    def test_valid_string_uuid_parsed(self):
        raw_uuid = uuid4()
        vo = CustomerId(str(raw_uuid))
        assert vo.value == raw_uuid

    def test_invalid_uuid_string(self):
        with pytest.raises(InvalidCustomerIdError):
            CustomerId("invalid-uuid-format")

    def test_invalid_type(self):
        with pytest.raises(InvalidCustomerIdError):
            CustomerId(12345)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = CustomerId()
        with pytest.raises(FrozenInstanceError):
            vo.value = uuid4()  # type: ignore[misc]

    def test_equality_by_value(self):
        raw_uuid = uuid4()
        vo1 = CustomerId(raw_uuid)
        vo2 = CustomerId(raw_uuid)
        vo3 = CustomerId(uuid4())
        assert vo1 == vo2
        assert vo1 != vo3

    def test_primitive_accessor(self):
        raw_uuid = uuid4()
        vo = CustomerId(raw_uuid)
        assert vo.value == raw_uuid
        assert str(vo) == str(raw_uuid)


class TestName:
    def test_valid_name(self):
        vo = Name("Alice Smith")
        assert vo.value == "Alice Smith"

    def test_invalid_empty_or_whitespace(self):
        with pytest.raises(InvalidNameError):
            Name("")
        with pytest.raises(InvalidNameError):
            Name("   ")

    def test_invalid_length_exceeded(self):
        with pytest.raises(InvalidNameError):
            Name("A" * 256)

    def test_invalid_type(self):
        with pytest.raises(InvalidNameError):
            Name(1234)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = Name("Alice")
        with pytest.raises(FrozenInstanceError):
            vo.value = "Bob"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert Name("Alice") == Name("Alice")
        assert Name("Alice") != Name("Bob")

    def test_primitive_accessor(self):
        vo = Name("Alice")
        assert vo.value == "Alice"


class TestEmail:
    def test_valid_email(self):
        vo = Email("alice@example.com")
        assert vo.value == "alice@example.com"

    def test_invalid_email_format(self):
        with pytest.raises(InvalidEmailError):
            Email("not-an-email")
        with pytest.raises(InvalidEmailError):
            Email("@missing-local.com")
        with pytest.raises(InvalidEmailError):
            Email("missing-domain@")

    def test_invalid_empty(self):
        with pytest.raises(InvalidEmailError):
            Email("")

    def test_invalid_type(self):
        with pytest.raises(InvalidEmailError):
            Email(123)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = Email("alice@example.com")
        with pytest.raises(FrozenInstanceError):
            vo.value = "bob@example.com"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert Email("a@b.com") == Email("a@b.com")
        assert Email("a@b.com") != Email("other@b.com")

    def test_primitive_accessor(self):
        vo = Email("alice@example.com")
        assert vo.value == "alice@example.com"


class TestLanguage:
    def test_valid_iso_639_1(self):
        vo = Language("en")
        assert vo.value == "en"

    def test_valid_bcp_47(self):
        vo = Language("en-US")
        assert vo.value == "en-US"

    def test_invalid_language(self):
        with pytest.raises(InvalidLanguageError):
            Language("invalid_lang")
        with pytest.raises(InvalidLanguageError):
            Language("123")

    def test_immutability(self):
        vo = Language("en")
        with pytest.raises(FrozenInstanceError):
            vo.value = "es"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert Language("es") == Language("es")
        assert Language("es") != Language("en")

    def test_primitive_accessor(self):
        vo = Language("es")
        assert vo.value == "es"


class TestCountry:
    def test_valid_country(self):
        vo = Country("ES")
        assert vo.value == "ES"

    def test_invalid_country(self):
        with pytest.raises(InvalidCountryError):
            Country("ESP")
        with pytest.raises(InvalidCountryError):
            Country("es")
        with pytest.raises(InvalidCountryError):
            Country("12")

    def test_immutability(self):
        vo = Country("ES")
        with pytest.raises(FrozenInstanceError):
            vo.value = "US"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert Country("US") == Country("US")
        assert Country("US") != Country("ES")

    def test_primitive_accessor(self):
        vo = Country("ES")
        assert vo.value == "ES"


class TestTimeZone:
    def test_valid_timezone(self):
        vo = TimeZone("Europe/Madrid")
        assert vo.value == "Europe/Madrid"
        utc_vo = TimeZone("UTC")
        assert utc_vo.value == "UTC"

    def test_invalid_timezone(self):
        with pytest.raises(InvalidTimeZoneError):
            TimeZone("Mars/Olympus")

    def test_immutability(self):
        vo = TimeZone("UTC")
        with pytest.raises(FrozenInstanceError):
            vo.value = "Europe/Madrid"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert TimeZone("UTC") == TimeZone("UTC")
        assert TimeZone("UTC") != TimeZone("Europe/Madrid")

    def test_primitive_accessor(self):
        vo = TimeZone("Europe/Madrid")
        assert vo.value == "Europe/Madrid"


class TestCreatedAt:
    def test_valid_default_utc(self):
        vo = CreatedAt()
        assert isinstance(vo.value, datetime)
        assert vo.value.tzinfo == timezone.utc

    def test_valid_explicit_utc(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        vo = CreatedAt(dt)
        assert vo.value == dt

    def test_invalid_naive_datetime(self):
        naive_dt = datetime(2026, 1, 1, 12, 0, 0)
        with pytest.raises(InvalidTimestampError):
            CreatedAt(naive_dt)

    def test_immutability(self):
        vo = CreatedAt()
        with pytest.raises(FrozenInstanceError):
            vo.value = datetime.now(timezone.utc)  # type: ignore[misc]

    def test_equality_by_value(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert CreatedAt(dt) == CreatedAt(dt)

    def test_primitive_accessor(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        vo = CreatedAt(dt)
        assert vo.value == dt


class TestCustomerEntity:
    def test_create_customer_with_vos(self):
        customer_id = CustomerId()
        created_at = CreatedAt()
        customer = Customer(
            id=customer_id,
            name=Name("Jane Doe"),
            email=Email("jane@example.com"),
            language=Language("en-US"),
            country=Country("US"),
            timezone=TimeZone("America/New_York"),
            created_at=created_at,
        )

        assert customer.id == customer_id
        assert customer.name == Name("Jane Doe")
        assert customer.email == Email("jane@example.com")
        assert customer.language == Language("en-US")
        assert customer.country == Country("US")
        assert customer.timezone == TimeZone("America/New_York")
        assert customer.created_at == created_at

        # Verify accessors
        assert customer.id.value == customer_id.value
        assert customer.name.value == "Jane Doe"
        assert customer.email.value == "jane@example.com"
        assert customer.language.value == "en-US"
        assert customer.country.value == "US"
        assert customer.timezone.value == "America/New_York"
        assert customer.created_at.value == created_at.value

    def test_create_customer_with_defaults(self):
        customer = Customer(
            name=Name("Jane Doe"),
            email=Email("jane@example.com"),
        )

        assert isinstance(customer.id, CustomerId)
        assert isinstance(customer.id.value, UUID)
        assert customer.name == Name("Jane Doe")
        assert customer.name.value == "Jane Doe"
        assert customer.email == Email("jane@example.com")
        assert customer.email.value == "jane@example.com"
        assert customer.language is None
        assert customer.country is None
        assert customer.timezone is None
        assert isinstance(customer.created_at, CreatedAt)
        assert customer.created_at.value.tzinfo == timezone.utc
