from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    tenant_id: str
    model_config = ConfigDict(from_attributes=True)


class DeckBase(BaseModel):
    pass


class DeckResponse(BaseModel):
    id: str
    created_at: datetime
    # ... other fields
    model_config = ConfigDict(from_attributes=True)


class AnalysisStart(BaseModel):
    template_version_id: str | None = None


class AnalysisResponse(BaseModel):
    id: str
    status: str
    score: int | None
    findings_count: int = 0
    model_config = ConfigDict(from_attributes=True)
