from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=80)
    avatar_url: HttpUrl | None = None
    bio: str | None = Field(default=None, max_length=1000)
    birth_date: date | None = None
    theme: str | None = Field(default=None, pattern="^(light|dark)$")
