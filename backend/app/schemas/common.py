from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
