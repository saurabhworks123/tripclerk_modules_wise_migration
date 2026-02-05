"""
Generic Response Models
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str


class DataResponse(BaseResponse):
    """Response with data"""
    data: Optional[Any] = None


class ListResponse(BaseResponse):
    """Response with list of items"""
    data: List[Any] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class FileUploadResponse(BaseResponse):
    """File upload response"""
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None


class NotificationResponse(BaseModel):
    """Notification model"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str  # info, warning, success, error
    link: Optional[str] = None
    is_read: bool = False
    created_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # asc or desc


class FilterParams(BaseModel):
    """Common filter parameters"""
    status: Optional[str] = None
    department: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
