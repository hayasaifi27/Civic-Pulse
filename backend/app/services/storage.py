import os
import uuid
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from supabase import create_client, Client

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.bucket = settings.supabase_storage_bucket
        self._init_client()

    def _init_client(self):
        if settings.supabase_url and settings.supabase_service_role_key:
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def _generate_path(self, user_id: Optional[uuid.UUID], file_name: str) -> str:
        ext = os.path.splitext(file_name)[1].lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        user_prefix = str(user_id) if user_id else "anonymous"
        return f"reports/{user_prefix}/{date_path}/{unique_name}"

    async def upload_file(
        self,
        file: UploadFile,
        user_id: Optional[uuid.UUID] = None
    ) -> dict:
        if not self.client:
            raise HTTPException(status_code=503, detail="Storage service not configured")

        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(status_code=400, detail=f"File size exceeds {settings.max_file_size} bytes")

        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

        path = self._generate_path(user_id, file.filename)
        
        try:
            self.client.storage.from_(self.bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": file.content_type, "upsert": "false"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        return {
            "storage_path": path,
            "file_name": file.filename,
            "mime_type": file.content_type,
            "file_size": len(content)
        }

    async def upload_bytes(
        self,
        content: bytes,
        file_name: str,
        mime_type: str,
        user_id: Optional[uuid.UUID] = None
    ) -> dict:
        if not self.client:
            raise HTTPException(status_code=503, detail="Storage service not configured")

        if len(content) > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File size exceeds limit")

        if mime_type not in settings.allowed_file_types:
            raise HTTPException(status_code=400, detail=f"File type {mime_type} not allowed")

        path = self._generate_path(user_id, file_name)
        
        try:
            self.client.storage.from_(self.bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": mime_type, "upsert": "false"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        return {
            "storage_path": path,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size": len(content)
        }

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        if not self.client:
            raise HTTPException(status_code=503, detail="Storage service not configured")
        
        try:
            return self.client.storage.from_(self.bucket).create_signed_url(path, expires_in)["signedURL"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")

    def get_public_url(self, path: str) -> str:
        if not self.client:
            return f"/media/{path}"
        return self.client.storage.from_(self.bucket).get_public_url(path)

    async def delete_file(self, path: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.storage.from_(self.bucket).remove([path])
            return True
        except Exception:
            return False


storage_service = StorageService()