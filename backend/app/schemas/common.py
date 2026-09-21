from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ResponseBase(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    pagination: Optional[Pagination] = None


class ListResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: List[T] = []


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None
