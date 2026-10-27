from typing import List
from fastapi import APIRouter, Depends, Query
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories import NotificationRepository
from app.schemas import NotificationResponse, NotificationChannel

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    repo = NotificationRepository(db)
    return await repo.get_user_notifications(current_user.id, unread_only=unread_only, limit=limit)


@router.get("/unread-count")
async def get_unread_count(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    repo = NotificationRepository(db)
    notifications = await repo.get_user_notifications(current_user.id, unread_only=True, limit=1000)
    return {"count": len(notifications)}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    repo = NotificationRepository(db)
    success = await repo.mark_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    repo = NotificationRepository(db)
    count = await repo.mark_all_read(current_user.id)
    return {"marked_read": count}