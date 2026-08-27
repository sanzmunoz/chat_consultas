from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.presentation.schemas.message_schemas import (
    SendMessageRequest,
    EditMessageRequest,
    MessageResponse,
    KeysetMessageListResponse,
    SearchMessageItemResponse
)
from src.presentation.schemas.common_schemas import SuccessResponse
from src.presentation.middleware.auth_middleware import get_current_user
from src.domain.entities.user import User
from src.application.messages.send_message_use_case import SendMessageUseCase
from src.application.messages.list_messages_keyset_use_case import ListMessagesKeysetUseCase
from src.application.messages.search_messages_use_case import SearchMessagesUseCase
from src.application.messages.edit_message_use_case import EditMessageUseCase
from src.application.messages.delete_message_use_case import DeleteMessageUseCase
from src.infrastructure.database.pg_message_repository import PgMessageRepository
from src.infrastructure.llm.openai_llm_service import OpenAILlmService

router = APIRouter(tags=["Mensajes"])

message_repo = PgMessageRepository()
llm_service = OpenAILlmService()

send_msg_uc = SendMessageUseCase(message_repo, llm_service)
list_msgs_uc = ListMessagesKeysetUseCase(message_repo)
search_msgs_uc = SearchMessagesUseCase(message_repo)
edit_msg_uc = EditMessageUseCase(message_repo)
delete_msg_uc = DeleteMessageUseCase(message_repo)

@router.get("/api/channels/{id}/messages", response_model=KeysetMessageListResponse, summary="Historial con Keyset Pagination")
async def list_channel_messages(
    id: UUID,
    cursor_created_at: Optional[datetime] = Query(None, description="Cursor fecha ISO UTC"),
    cursor_id: Optional[UUID] = Query(None, description="Cursor ID UUID v4"),
    limit: int = Query(20, ge=1, le=100, description="Límite de mensajes por página"),
    current_user: User = Depends(get_current_user)
):
    """
    Consulta 1: Retorna mensajes con paginación por keyset indexada (O(1)).
    """
    messages = await list_msgs_uc.execute(
        actor_id=current_user.id,
        channel_id=id,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
        limit=limit
    )

    msg_responses = [
        MessageResponse(
            id=m.id,
            msg_ref=m.msg_ref,
            channel_id=m.channel_id,
            author_id=m.author_id,
            author_name=m.author_name,
            author_username=m.author_username,
            author_position=m.author_position,
            content=m.content,
            original_content=m.original_content,
            status=m.status,
            is_edited=m.is_edited,
            edited_at=m.edited_at,
            is_deleted=m.is_deleted,
            created_at=m.created_at,
            read_count=m.read_count,
            is_read_by_me=m.is_read_by_me
        )
        for m in messages
    ]

    next_cursor_at = messages[-1].created_at if messages else None
    next_cursor_id = messages[-1].id if messages else None
    has_more = len(messages) == limit

    return KeysetMessageListResponse(
        messages=msg_responses,
        next_cursor_created_at=next_cursor_at,
        next_cursor_id=next_cursor_id,
        has_more=has_more
    )

@router.get("/api/messages/search", response_model=List[SearchMessageItemResponse], summary="Búsqueda Full-Text con Resaltado")
async def search_messages(
    q: str = Query(..., min_length=1, description="Término de búsqueda léxica"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Consulta 2: Búsqueda léxica full-text con resaltado del término encontrado (ts_headline).
    """
    results = await search_msgs_uc.execute(current_user.id, q, limit)
    return [
        SearchMessageItemResponse(
            id=m.id,
            msg_ref=m.msg_ref,
            channel_id=m.channel_id,
            channel_name=m.author_position.split(" | ")[0] if m.author_position and " | " in m.author_position else "Canal",
            author_id=m.author_id,
            author_name=m.author_name or "",
            author_username=m.author_username or "",
            content=m.content,
            highlighted_content=m.highlighted_content,
            search_rank=m.search_rank or 0.0,
            created_at=m.created_at
        )
        for m in results
    ]

@router.post("/api/channels/{id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, summary="Enviar mensaje atómico")
async def send_message(
    id: UUID,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Envío atómico de mensaje validando membresía y generando embeddings.
    """
    try:
        new_msg_id = await send_msg_uc.execute(
            actor_id=current_user.id,
            channel_id=id,
            content=req.content,
            status=req.status,
            msg_ref=req.msg_ref
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo enviar el mensaje: {str(e)}"
        )

    # Fetch created message to return complete representation
    msgs = await list_msgs_uc.execute(current_user.id, id, limit=1)
    if msgs and msgs[0].id == new_msg_id:
        m = msgs[0]
        return MessageResponse(
            id=m.id,
            msg_ref=m.msg_ref,
            channel_id=m.channel_id,
            author_id=m.author_id,
            author_name=m.author_name,
            author_username=m.author_username,
            author_position=m.author_position,
            content=m.content,
            original_content=m.original_content,
            status=m.status,
            is_edited=m.is_edited,
            edited_at=m.edited_at,
            is_deleted=m.is_deleted,
            created_at=m.created_at,
            read_count=m.read_count,
            is_read_by_me=True
        )

    return MessageResponse(
        id=new_msg_id,
        channel_id=id,
        author_id=current_user.id,
        author_name=current_user.display_name,
        author_username=current_user.username,
        author_position=current_user.position,
        content=req.content,
        status=req.status,
        is_edited=False,
        is_deleted=False,
        created_at=datetime.utcnow()
    )

@router.patch("/api/messages/{id}", response_model=SuccessResponse, summary="Editar mensaje")
async def edit_message(
    id: UUID,
    req: EditMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Edita mensaje preservando original_content.
    """
    try:
        success = await edit_msg_uc.execute(current_user.id, id, req.content)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo editar el mensaje.")
        return SuccessResponse(message="Mensaje editado correctamente.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/api/messages/{id}", response_model=SuccessResponse, summary="Eliminación lógica de mensaje")
async def delete_message(
    id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Elimina lógicamente un mensaje (is_deleted = TRUE).
    """
    try:
        success = await delete_msg_uc.execute(current_user.id, id)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el mensaje.")
        return SuccessResponse(message="Mensaje eliminado lógicamente.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
