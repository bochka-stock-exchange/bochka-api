from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class InstrumentCreate(BaseModel):
    ticker: Annotated[str, Field(pattern="^[A-Z]{2,10}$")]
    name: Annotated[str, Field(max_length=255)]


class InstrumentRead(BaseModel):
    ticker: str
    name: str
    model_config = ConfigDict(from_attributes=True)
