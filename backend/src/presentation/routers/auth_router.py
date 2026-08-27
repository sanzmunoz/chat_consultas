from fastapi import APIRouter, HTTPException, status, Depends
from src.presentation.schemas.auth_schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse
)
from src.presentation.middleware.auth_middleware import get_current_user
from src.domain.entities.user import User
from src.application.auth.login_use_case import LoginUseCase
from src.application.auth.refresh_use_case import RefreshUseCase
from src.infrastructure.database.pg_user_repository import PgUserRepository

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

user_repo = PgUserRepository()
login_uc = LoginUseCase(user_repo)
refresh_uc = RefreshUseCase(user_repo)

@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
async def login(req: LoginRequest):
    result = await login_uc.execute(req.username_or_email, req.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o cuenta de usuario inactiva."
        )
    return result

@router.post("/refresh", response_model=TokenResponse, summary="Rotar refresh token")
async def refresh(req: RefreshTokenRequest):
    result = await refresh_uc.execute(req.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido, expirado o revocado."
        )
    return result

@router.get("/me", response_model=UserProfileResponse, summary="Perfil del usuario autenticado")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        position=current_user.position
    )
