import ql
from pydantic import BaseModel


@ql.model
class Point(BaseModel):
    x: int
    y: int
