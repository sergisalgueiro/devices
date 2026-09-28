from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class DomainResponseBase(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def unwrap_value_objects(cls, data: Any) -> Any:
        if hasattr(data, "__dataclass_fields__"):
            return {
                field_name: getattr(field_val, "value", field_val)
                for field_name, field_val in (
                    (f, getattr(data, f)) for f in data.__dataclass_fields__
                )
            }
        return data
