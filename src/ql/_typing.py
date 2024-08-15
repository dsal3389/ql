from typing import Optional, TypedDict, Any


class QueryErrorLocationDict(TypedDict):
    line: int
    column: int


class QueryErrorDict(TypedDict):
    message: str
    locations: list[QueryErrorLocationDict]


class QueryResponseDict(TypedDict):
    data: Optional[dict[Any, Any]]
    errors: Optional[list[QueryErrorDict]]


class QLFieldMetadata:
    """
    metadata class used for pydantic class fields with `Annotated`
    type

    @ql.model
    class Foo(BaseModel):
        my_field: Annotated[str, ql.metadata(query_name="foo")]
    """

    __slots__ = ("query_name", "mutate_name", "queryable", "mutable")

    def __init__(
        self,
        query_name: Optional[str] = None,
        mutate_name: Optional[str] = None,
        queryable: bool = True,
        mutable: bool = True,
    ) -> None:
        self.query_name = query_name
        self.queryable = queryable

        self.mutate_name = mutate_name
        self.mutable = mutable


def metadata(
    query_name: Optional[str] = None,
    mutate_name: Optional[str] = None,
    queryable: bool = True,
    mutable: bool = True,
) -> QLFieldMetadata:
    return QLFieldMetadata(
        query_name=query_name,
        mutate_name=mutate_name,
        queryable=queryable,
        mutable=mutable,
    )
