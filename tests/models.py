import ql
from pydantic import BaseModel


@ql.model
class Point(BaseModel):
    x: int
    y: int


@ql.model
class Human(BaseModel):
    first_name: str
    last_name: str
    aliva: bool


@ql.model
class Male(Human):
    sick: bool


@ql.model
class Female(Human):
    pregnant: bool


@ql.model
class Child(Human):
    playing: bool


@ql.model(query_name="family")
class Family(BaseModel):
    people: list[Male | Female | Child]
    count: int
