from datetime import date

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255, pattern=r"^.+@.+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255, pattern=r"^.+@.+$")
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    birth_date: date | None = None
    theme: str = "light"
    balance_cents: int = 0
    email_verified: bool = False


class AuthResponse(BaseModel):
    user: UserResponse
    csrf_token: str
