from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.watch_room import WatchParticipantRole, WatchRoomStatus


class WatchRoomCreate(BaseModel):
    movie_id: UUID = Field(validation_alias=AliasChoices("movieId", "movie_id"), serialization_alias="movieId")
    club_id: int | None = Field(default=None, gt=0, validation_alias=AliasChoices("clubId", "club_id"), serialization_alias="clubId")

    model_config = ConfigDict(extra="forbid")


class WatchParticipantRead(BaseModel):
    user_id: int = Field(serialization_alias="userId")
    nickname: str
    role: WatchParticipantRole

    model_config = ConfigDict(from_attributes=True)


class WatchRoomCreated(BaseModel):
    id: UUID
    code: str
    movie_id: UUID = Field(serialization_alias="movieId")
    status: WatchRoomStatus

    model_config = ConfigDict(from_attributes=True)


class WatchRoomRead(WatchRoomCreated):
    participants: list[WatchParticipantRead]


class WatchRoomJoin(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")


class WatchRoomJoinResult(BaseModel):
    room_id: UUID = Field(serialization_alias="roomId")
    joined: bool = True
