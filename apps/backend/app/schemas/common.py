from typing import Annotated
from uuid import UUID

from pydantic import BeforeValidator


def _empty_to_none(v: object) -> object:
    if v is None or v == "":
        return None
    return v


OptionalUUID = Annotated[UUID | None, BeforeValidator(_empty_to_none)]
