from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ShopOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    is_active: bool


class ShopCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: Optional[str] = Field(default=None, max_length=150)
    description: str = ""


class ShopUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MembershipOut(BaseModel):
    id: int
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool


class MembershipRoleIn(BaseModel):
    role: str


class InvitationIn(BaseModel):
    email: str
    role: str = "customer"


class InvitationOut(BaseModel):
    detail: str
    expires_at: datetime


class MessageOut(BaseModel):
    detail: str
