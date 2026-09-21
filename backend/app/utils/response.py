from typing import Any, Optional, List
from app.schemas.common import ResponseBase, PaginatedResponse, Pagination


def success_response(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def paginated_response(data: Any, page: int, page_size: int, total: int, message: str = "success") -> dict:
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "code": 0,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    }


def error_response(code: int, message: str, detail: Optional[str] = None) -> dict:
    resp = {"code": code, "message": message}
    if detail:
        resp["detail"] = detail
    return resp
