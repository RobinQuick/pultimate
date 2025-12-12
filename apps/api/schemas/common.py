from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

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
    template_version_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    id: str
    status: str
    score: Optional[int]
    findings_count: int = 0
    model_config = ConfigDict(from_attributes=True)
