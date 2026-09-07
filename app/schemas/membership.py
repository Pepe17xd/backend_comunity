from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.membership import MembershipRole


class MembershipRoleUpdate(BaseModel):
    role: MembershipRole


class MembershipRead(BaseModel):
    id: int
    user_id: int
    club_id: int
    role: MembershipRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
