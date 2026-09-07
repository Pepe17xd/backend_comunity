from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.membership import MembershipRole
from app.models.user import User
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate
from app.services.club_service import ClubService
from app.services.membership_service import MembershipService

router = APIRouter()


@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club(
    payload: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClubService(db).create_club(payload, owner_id=current_user.id)


@router.get("", response_model=list[ClubRead])
def list_clubs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ClubService(db).list_clubs(skip=skip, limit=limit)


@router.get("/{club_id}", response_model=ClubRead)
def get_club(club_id: int, db: Session = Depends(get_db)):
    club = ClubService(db).get_club(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club no encontrado")
    return club


@router.put("/{club_id}", response_model=ClubRead)
def update_club(
    club_id: int,
    payload: ClubUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    MembershipService(db).require_role(
        club_id, current_user.id, {MembershipRole.OWNER, MembershipRole.ADMIN}
    )
    return ClubService(db).update_club(club_id, payload)


@router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    MembershipService(db).require_role(
        club_id, current_user.id, {MembershipRole.OWNER}
    )
    ClubService(db).deactivate_club(club_id)
