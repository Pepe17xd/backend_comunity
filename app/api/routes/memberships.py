from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.membership import MembershipRole
from app.models.user import User
from app.schemas.membership import MembershipRead, MembershipRoleUpdate
from app.services.membership_service import MembershipService

router = APIRouter()


@router.post(
    "/clubs/{club_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def join_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MembershipService(db).join_club(club_id, current_user.id)


@router.get("/clubs/{club_id}/members", response_model=list[MembershipRead])
def list_club_members(club_id: int, db: Session = Depends(get_db)):
    return MembershipService(db).list_club_members(club_id)


@router.get("/users/{user_id}/clubs", response_model=list[MembershipRead])
def list_user_clubs(user_id: int, db: Session = Depends(get_db)):
    return MembershipService(db).list_user_memberships(user_id)


@router.patch(
    "/clubs/{club_id}/members/{user_id}/role",
    response_model=MembershipRead,
)
def change_member_role(
    club_id: int,
    user_id: int,
    payload: MembershipRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MembershipService(db)
    service.require_role(club_id, current_user.id, {MembershipRole.OWNER})
    return service.change_role(club_id, user_id, payload.role)


@router.delete(
    "/clubs/{club_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def leave_or_remove_member(
    club_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MembershipService(db)

    if current_user.id != user_id:
        service.require_role(
            club_id,
            current_user.id,
            {MembershipRole.OWNER, MembershipRole.ADMIN},
        )

    service.leave_club(club_id, user_id)
