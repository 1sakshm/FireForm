from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_db
from app.api.schemas.profiles import ProfileCreate, ProfileResponse, ProfileUpdate
from app.models.models import Profile

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/", response_model=ProfileResponse | None)
def get_current_profile(db: Session = Depends(get_db)):
    return db.exec(select(Profile).order_by(Profile.updated_at.desc())).first()


@router.post("/", response_model=ProfileResponse, status_code=201)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    db_profile = Profile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: UUID, db: Session = Depends(get_db)):
    db_profile = db.exec(select(Profile).where(Profile.profile_id == profile_id)).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile


@router.patch("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: UUID, profile_update: ProfileUpdate, db: Session = Depends(get_db)):
    db_profile = db.exec(select(Profile).where(Profile.profile_id == profile_id)).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
    db_profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(db_profile)
    return db_profile