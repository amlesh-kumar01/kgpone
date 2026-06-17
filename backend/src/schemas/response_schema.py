from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: T | None = None
