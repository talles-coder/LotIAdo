"""Pydantic schemas for the identity module's HTTP interface."""
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
