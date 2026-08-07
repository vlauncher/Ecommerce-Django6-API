from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any


class MessageOut(BaseModel):
    detail: str


class RegisterIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
    accept_terms: bool = False
    accept_privacy: bool = False


class VerifyOTPIn(BaseModel):
    otp: str = Field(min_length=6, max_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ResendOTPIn(BaseModel):
    email: EmailStr
    purpose: str = "register"


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8)
    confirm_password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str


class DeleteAccountIn(BaseModel):
    password: str


class RefreshTokenIn(BaseModel):
    refresh: str


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_verified: bool


class TokenOut(BaseModel):
    access: str
    refresh: str
    user: UserOut


class UserProfileUpdateIn(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None


class UserProfileOut(BaseModel):
    id: int
    user: UserOut
    age: Optional[int] = None
    sex: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    profile_pic_url: Optional[str] = None
