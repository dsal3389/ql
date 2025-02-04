from typing import TypedDict, Any
from typing_extensions import NotRequired


class QueryErrorLocationDict(TypedDict):
    line: int
    column: int


class QueryErrorDict(TypedDict):
    message: str
    locations: list[QueryErrorLocationDict]


class QueryResponseDict(TypedDict):
    data: dict[Any, Any] | None
    errors: NotRequired[list[QueryErrorDict]]


class QLFieldMetadata:
    """
    metadata class used for pydantic class fields with `Annotated`
    type

    @ql.model
    class Foo(BaseModel):
        my_field: Annotated[str, ql.metadata(query_name="foo")]
    """

    __slots__ = ("query_name", "queryable", "mutate_name", "mutable")

    def __init__(
        self,
        query_name: str | None = None,
        queryable: bool = True,
        mutate_name: str | None = None,
        mutable: bool = True,
    ) -> None:
        self.query_name = query_name
        self.mutate_name = mutate_name
        self.queryable = queryable
        self.mutable = mutable


def metadata(
    query_name: str | None = None,
    mutate_name: str | None = None,
    *,
    queryable: bool = True,
    mutable: bool = True,
) -> QLFieldMetadata:
    return QLFieldMetadata(
        mutate_name=mutate_name,
        query_name=query_name,
        queryable=queryable,
        mutable=mutable,
    )
