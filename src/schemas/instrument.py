from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class InstrumentBase(BaseModel):
    ticker: Annotated[str, Field(pattern="^[A-Z]{2,10}$")]
    name: Annotated[str, Field(max_length=255)]


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentRead(InstrumentBase):
    model_config = ConfigDict(from_attributes=True)
