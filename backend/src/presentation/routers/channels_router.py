from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from src.presentation.schemas.channel_schemas import ChannelSummaryResponse, ChannelMemberResponse
from src.presentation.middleware.auth_middleware import get_current_user
from src.domain.entities.user import User
from src.application.channels.list_user_channels_use_case import ListUserChannelsUseCase
from src.application.channels.get_channel_members_use_case import GetChannelMembersUseCase
from src.infrastructure.database.pg_channel_repository import PgChannelRepository

router = APIRouter(prefix="/api/channels", tags=["Canales"])

channel_repo = PgChannelRepository()
list_channels_uc = ListUserChannelsUseCase(channel_repo)
get_members_uc = GetChannelMembersUseCase(channel_repo)

@router.get("", response_model=List[ChannelSummaryResponse], summary="Listar canales del usuario")
async def list_channels(current_user: User = Depends(get_current_user)):
    """
    Retorna la lista de canales accesibles por el usuario con contadores
    de mensajes no leídos y vista previa del último mensaje.
    """
    summaries = await list_channels_uc.execute(current_user.id)
    return [
        ChannelSummaryResponse(
            channel_id=s.channel_id,
            channel_name=s.channel_name,
            channel_description=s.channel_description,
            channel_type=s.channel_type,
            is_archived=s.is_archived,
            user_channel_role=s.user_channel_role,
            member_count=s.member_count,
            unread_count=s.unread_count,
            last_message_id=s.last_message_id,
            last_message_content=s.last_message_content,
            last_message_created_at=s.last_message_created_at,
            last_message_author_name=s.last_message_author_name
        )
        for s in summaries
    ]

@router.get("/{id}/members", response_model=List[ChannelMemberResponse], summary="Obtener miembros de un canal")
async def get_channel_members(id: UUID, current_user: User = Depends(get_current_user)):
    """
    Retorna los miembros del canal especificado si el usuario tiene acceso.
    """
    members = await get_members_uc.execute(id, current_user.id)
    return [
        ChannelMemberResponse(
            membership_id=m["membership_id"],
            user_id=m["user_id"],
            display_name=m["display_name"],
            username=m["username"],
            email=m["email"],
            position=m["position"],
            role=m["role"],
            joined_at=m["joined_at"]
        )
        for m in members
    ]
