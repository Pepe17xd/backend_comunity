from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.club import ClubVisibility


class ClubCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str | None = None
    visibility: ClubVisibility = ClubVisibility.PUBLIC


class ClubUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = None
    visibility: ClubVisibility | None = None


class ClubRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    visibility: ClubVisibility
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
