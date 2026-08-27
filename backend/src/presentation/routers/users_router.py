from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.presentation.schemas.user_schemas import (
    UserItemResponse,
    UserListResponse,
    EditUserRequest
)
from src.presentation.schemas.common_schemas import SuccessResponse
from src.presentation.middleware.auth_middleware import get_current_user, require_admin
from src.domain.entities.user import User
from src.application.users.list_users_use_case import ListUsersUseCase
from src.application.users.edit_delete_user_use_case import EditDeleteUserUseCase
from src.infrastructure.database.pg_user_repository import PgUserRepository

router = APIRouter(prefix="/api/users", tags=["Usuarios"])

user_repo = PgUserRepository()
list_users_uc = ListUsersUseCase(user_repo)
edit_delete_uc = EditDeleteUserUseCase(user_repo)

@router.get("", response_model=UserListResponse, summary="Consultar usuarios con métricas")
async def list_users(
    search: Optional[str] = Query(None, description="Filtro de búsqueda por nombre, email o cargo"),
    role: Optional[str] = Query(None, pattern="^(admin|member)$", description="Filtro por rol"),
    cursor_created_at: Optional[datetime] = Query(None, description="Cursor fecha"),
    cursor_id: Optional[UUID] = Query(None, description="Cursor ID"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Invoca procedimiento almacenado rw_sp_query_users con métricas de canales y mensajes.
    """
    results = await list_users_uc.execute(
        search=search,
        role=role,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
        limit=limit
    )

    items = [
        UserItemResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            position=u.position,
            is_active=u.is_active,
            created_at=u.created_at,
            channels_count=c_count,
            messages_count=m_count
        )
        for u, c_count, m_count in results
    ]

    next_cursor_at = results[-1][0].created_at if results else None
    next_cursor_id = results[-1][0].id if results else None

    return UserListResponse(
        users=items,
        next_cursor_created_at=next_cursor_at,
        next_cursor_id=next_cursor_id
    )

@router.patch("/{id}", response_model=SuccessResponse, summary="Editar perfil de usuario")
async def edit_user(
    id: UUID,
    req: EditUserRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Invoca procedimiento almacenado rw_sp_edit_or_delete_user ('EDIT').
    """
    # Authorization: User can edit own profile, Admin can edit anyone
    if current_user.id != id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar el perfil de otro usuario."
        )

    # Only admin can alter roles
    if req.role and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden cambiar roles de usuario."
        )

    success, msg = await edit_delete_uc.execute(
        actor_id=current_user.id,
        target_user_id=id,
        action="EDIT",
        display_name=req.display_name,
        position=req.position,
        role=req.role
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return SuccessResponse(message=msg)

@router.delete("/{id}", response_model=SuccessResponse, summary="Desactivar usuario (Admin)")
async def deactivate_user(
    id: UUID,
    current_admin: User = Depends(require_admin)
):
    """
    Invoca procedimiento almacenado rw_sp_edit_or_delete_user ('DELETE').
    Desactiva al usuario y revoca sus sesiones de refresh token.
    """
    if current_admin.id == id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta de administrador."
        )

    success, msg = await edit_delete_uc.execute(
        actor_id=current_admin.id,
        target_user_id=id,
        action="DELETE"
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return SuccessResponse(message=msg)
