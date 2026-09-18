"""Pydantic schemas for the identity module's HTTP interface."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    tenant_id: UUID | None


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: str


class InvitationResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class InvitationAcceptRequest(BaseModel):
    full_name: str
    password: str


class InvitationAcceptResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None

    model_config = {"from_attributes": True}
