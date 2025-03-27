from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app import models


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=255)]


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: UUID
    role: models.UserRole
    api_key: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
