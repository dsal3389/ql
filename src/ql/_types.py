from pydantic import BaseModel
from typing import TypeVar


QLModel = TypeVar("QLModel", bound=BaseModel)
