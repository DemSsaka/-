from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import to_user_response
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.auth import UserResponse
from app.schemas.profile import ProfileUpdateRequest

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "avatar_url" and value is not None:
            value = str(value)
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return to_user_response(current_user)
