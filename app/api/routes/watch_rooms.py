from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.watch_room import WatchRoomCreate, WatchRoomCreated, WatchRoomJoin, WatchRoomJoinResult, WatchRoomRead
from app.services.watch_room_service import WatchRoomService

router = APIRouter()


@router.post("", response_model=WatchRoomCreated, status_code=status.HTTP_201_CREATED)
def create_watch_room(
    payload: WatchRoomCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return WatchRoomService(db).create_room(payload, current_user)


@router.get("/{code}", response_model=WatchRoomRead)
def get_watch_room(code: str, db: Session = Depends(get_db)):
    return WatchRoomService(db).get_room(code)


@router.post("/{code}/join", response_model=WatchRoomJoinResult)
def join_watch_room(
    code: str, payload: WatchRoomJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    room = WatchRoomService(db).join_room(code, payload, current_user)
    return WatchRoomJoinResult(room_id=room.id)


@router.delete("/{code}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def leave_watch_room(
    code: str, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    WatchRoomService(db).leave_room(code, user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
