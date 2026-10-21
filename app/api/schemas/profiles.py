from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ProfileBase(BaseModel):
    name: str = Field(..., description="Name of the person filling the form")
    profession: str = Field(..., description="Profession of the person")
    role: str = Field(..., description="Role of the person")
    description: str | None = Field(None, description="Optional profile description")
    custom_fields: dict | None = Field(default_factory=dict, description="Extensible fields")

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    name: str | None = None
    profession: str | None = None
    role: str | None = None

class ProfileResponse(ProfileBase):
    profile_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
