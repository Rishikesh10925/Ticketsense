from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.platform import Organization
from app.schemas.auth import Token, UserCreate, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Self-service registration is Customer only. Elevated accounts are provisioned by admins.
    # are created via the seed/admin path, not this endpoint.
    tenant = await db.scalar(select(Organization).where(Organization.slug == "ticketsense-demo"))
    if tenant is None:
        raise HTTPException(status_code=503, detail="No registration tenant is configured")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role="customer",
        tenant_id=tenant.id,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    user = await db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.role, user.department_id, user.tenant_id)
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
