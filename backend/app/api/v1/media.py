import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.storage import storage_service
from app.repositories import ReportMediaRepository
from app.models import ReportMedia
from app.schemas import MediaUploadResponse

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    report_id: uuid.UUID = Form(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await storage_service.upload_file(file, current_user.id)
    
    media = ReportMedia(
        report_id=report_id,
        storage_path=result["storage_path"],
        file_name=result["file_name"],
        mime_type=result["mime_type"],
        file_size=result["file_size"]
    )
    
    media_repo = ReportMediaRepository(db)
    await media_repo.create(media)
    
    if report_id:
        report_media = await media_repo.get_by_report(report_id)
        if len(report_media) == 1:
            await media_repo.set_primary(report_id, media.id)
    
    return MediaUploadResponse(
        id=media.id,
        storage_path=media.storage_path,
        file_name=media.file_name,
        mime_type=media.mime_type,
        file_size=media.file_size,
        upload_url=storage_service.get_signed_url(media.storage_path)
    )


@router.get("/{media_id}")
async def get_media(
    media_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    media_repo = ReportMediaRepository(db)
    media = await media_repo.get_by_id(media_id)
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    signed_url = storage_service.get_signed_url(media.storage_path)
    return {"url": signed_url, "media": media}