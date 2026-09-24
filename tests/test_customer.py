from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.customer import Customer
from app.domain.exceptions import (
    InvalidCreatedAtError,
    InvalidCustomerCountryError,
    InvalidCustomerEmailError,
    InvalidCustomerIdError,
    InvalidCustomerLanguageError,
    InvalidCustomerNameError,
    InvalidCustomerTimeZoneError,
)
from app.domain.value_objects import (
    CreatedAt,
    CustomerCountry,
    CustomerEmail,
    CustomerId,
    CustomerLanguage,
    CustomerName,
    CustomerTimeZone,
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


class TestCustomerName:
    def test_valid_name(self):
        vo = CustomerName("Alice Smith")
        assert vo.value == "Alice Smith"

    def test_invalid_empty_or_whitespace(self):
        with pytest.raises(InvalidCustomerNameError):
            CustomerName("")
        with pytest.raises(InvalidCustomerNameError):
            CustomerName("   ")

    def test_invalid_length_exceeded(self):
        with pytest.raises(InvalidCustomerNameError):
            CustomerName("A" * 256)

    def test_invalid_type(self):
        with pytest.raises(InvalidCustomerNameError):
            CustomerName(1234)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = CustomerName("Alice")
        with pytest.raises(FrozenInstanceError):
            vo.value = "Bob"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert CustomerName("Alice") == CustomerName("Alice")
        assert CustomerName("Alice") != CustomerName("Bob")

    def test_primitive_accessor(self):
        vo = CustomerName("Alice")
        assert vo.value == "Alice"


class TestCustomerEmail:
    def test_valid_email(self):
        vo = CustomerEmail("alice@example.com")
        assert vo.value == "alice@example.com"

    def test_invalid_email_format(self):
        with pytest.raises(InvalidCustomerEmailError):
            CustomerEmail("not-an-email")
        with pytest.raises(InvalidCustomerEmailError):
            CustomerEmail("@missing-local.com")
        with pytest.raises(InvalidCustomerEmailError):
            CustomerEmail("missing-domain@")

    def test_invalid_empty(self):
        with pytest.raises(InvalidCustomerEmailError):
            CustomerEmail("")

    def test_invalid_type(self):
        with pytest.raises(InvalidCustomerEmailError):
            CustomerEmail(123)  # type: ignore[arg-type]

    def test_immutability(self):
        vo = CustomerEmail("alice@example.com")
        with pytest.raises(FrozenInstanceError):
            vo.value = "bob@example.com"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert CustomerEmail("a@b.com") == CustomerEmail("a@b.com")
        assert CustomerEmail("a@b.com") != CustomerEmail("other@b.com")

    def test_primitive_accessor(self):
        vo = CustomerEmail("alice@example.com")
        assert vo.value == "alice@example.com"


class TestCustomerLanguage:
    def test_valid_iso_639_1(self):
        vo = CustomerLanguage("en")
        assert vo.value == "en"

    def test_valid_bcp_47(self):
        vo = CustomerLanguage("en-US")
        assert vo.value == "en-US"

    def test_invalid_language(self):
        with pytest.raises(InvalidCustomerLanguageError):
            CustomerLanguage("invalid_lang")
        with pytest.raises(InvalidCustomerLanguageError):
            CustomerLanguage("123")

    def test_immutability(self):
        vo = CustomerLanguage("en")
        with pytest.raises(FrozenInstanceError):
            vo.value = "es"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert CustomerLanguage("es") == CustomerLanguage("es")
        assert CustomerLanguage("es") != CustomerLanguage("en")

    def test_primitive_accessor(self):
        vo = CustomerLanguage("es")
        assert vo.value == "es"


class TestCustomerCountry:
    def test_valid_country(self):
        vo = CustomerCountry("ES")
        assert vo.value == "ES"

    def test_invalid_country(self):
        with pytest.raises(InvalidCustomerCountryError):
            CustomerCountry("ESP")
        with pytest.raises(InvalidCustomerCountryError):
            CustomerCountry("es")
        with pytest.raises(InvalidCustomerCountryError):
            CustomerCountry("12")

    def test_immutability(self):
        vo = CustomerCountry("ES")
        with pytest.raises(FrozenInstanceError):
            vo.value = "US"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert CustomerCountry("US") == CustomerCountry("US")
        assert CustomerCountry("US") != CustomerCountry("ES")

    def test_primitive_accessor(self):
        vo = CustomerCountry("ES")
        assert vo.value == "ES"


class TestCustomerTimeZone:
    def test_valid_timezone(self):
        vo = CustomerTimeZone("Europe/Madrid")
        assert vo.value == "Europe/Madrid"
        utc_vo = CustomerTimeZone("UTC")
        assert utc_vo.value == "UTC"

    def test_invalid_timezone(self):
        with pytest.raises(InvalidCustomerTimeZoneError):
            CustomerTimeZone("Mars/Olympus")

    def test_immutability(self):
        vo = CustomerTimeZone("UTC")
        with pytest.raises(FrozenInstanceError):
            vo.value = "Europe/Madrid"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert CustomerTimeZone("UTC") == CustomerTimeZone("UTC")
        assert CustomerTimeZone("UTC") != CustomerTimeZone("Europe/Madrid")

    def test_primitive_accessor(self):
        vo = CustomerTimeZone("Europe/Madrid")
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
        with pytest.raises(InvalidCreatedAtError):
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
            name=CustomerName("Jane Doe"),
            email=CustomerEmail("jane@example.com"),
            language=CustomerLanguage("en-US"),
            country=CustomerCountry("US"),
            timezone=CustomerTimeZone("America/New_York"),
            created_at=created_at,
        )

        assert customer.id == customer_id
        assert customer.name == CustomerName("Jane Doe")
        assert customer.email == CustomerEmail("jane@example.com")
        assert customer.language == CustomerLanguage("en-US")
        assert customer.country == CustomerCountry("US")
        assert customer.timezone == CustomerTimeZone("America/New_York")
        assert customer.created_at == created_at

        # Verify accessors
        assert customer.id.value == customer_id.value
        assert customer.name.value == "Jane Doe"
        assert customer.email.value == "jane@example.com"
        assert customer.language.value == "en-US"
        assert customer.country.value == "US"
        assert customer.timezone.value == "America/New_York"
        assert customer.created_at.value == created_at.value

    def test_create_customer_defaults_and_primitive_coercion(self):
        customer = Customer(name="Jane Doe", email="jane@example.com")

        assert isinstance(customer.id, CustomerId)
        assert isinstance(customer.id.value, UUID)
        assert customer.name == CustomerName("Jane Doe")
        assert customer.name.value == "Jane Doe"
        assert customer.email == CustomerEmail("jane@example.com")
        assert customer.email.value == "jane@example.com"
        assert customer.language is None
        assert customer.country is None
        assert customer.timezone is None
        assert isinstance(customer.created_at, CreatedAt)
        assert customer.created_at.value.tzinfo == timezone.utc

    def test_customer_validation_error_on_invalid_data(self):
        with pytest.raises(InvalidCustomerEmailError):
            Customer(name="Jane Doe", email="invalid-email")

        with pytest.raises(InvalidCustomerNameError):
            Customer(name="", email="jane@example.com")
