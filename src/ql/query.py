import enum
from inspect import isclass
from itertools import chain
from collections.abc import Iterable
from typing import Generator, TypeAlias, Any
from pydantic import BaseModel

from ._const import QL_QUERY_NAME_ATTR, QL_TYPENAME_ATTR
from .http import http


class _QueryOperationType(enum.Enum):
    ARGUMENTS = enum.auto()
    INLINE_FRAGMENT = enum.auto()
    REFERENCE_FRAGMENT = enum.auto()

    def __str__(self) -> str:
        return self.name


# list of operations that are allowed
# to be defined in query fields
_ALLOWED_FIELD_OPERATIONS = (_QueryOperationType.REFERENCE_FRAGMENT,)


class _QueryOperation:
    __slots__ = ("op", "model", "extra")

    def __init__(
        self,
        op: _QueryOperationType,
        model: type[BaseModel],
        extra: dict[Any, Any] = {},
    ) -> None:
        if not issubclass(model, BaseModel):
            raise TypeError(
                f"given model for operation `{op}` function does not inhertie from `pydantic.BaseModel`, model: `{model}`"
            )
        self.op = op
        self.model = model
        self.extra = extra


_QueryModelType: TypeAlias = tuple[
    type[BaseModel] | _QueryOperation,
    Iterable["str | _QueryModelType | _QueryOperation"],
]


class _QuerySerializer:
    __slots__ = ("_query", "_include_typename")

    def __init__(
        self, query_models: tuple[_QueryModelType, ...], include_typename: bool
    ) -> None:
        self._query = query_models
        self._include_typename = include_typename

    def serialize(self) -> str:
        return "".join(self._serialize_query())

    def _serialize_query(self) -> Generator[str, None, None]:
        yield "query{"
        for model_query in self._query:
            yield from self._serialize_model_query(model_query)
        yield "}"

    def _serialize_model_query(
        self, model_query: _QueryModelType
    ) -> Generator[str, None, None]:
        model_or_op, fields = model_query

        # if fields is a list or something that is not
        # iterable, then make it iterable
        if isinstance(fields, str) or not isinstance(fields, Iterable):
            fields = (fields,)

        # everytime we querying a model, we need to
        # check if we also need to query the `__typename` field
        if self._include_typename:
            fields = chain(fields, ("__typename",))

        yield from self._serialize_model_or_operation(model_or_op)
        yield "{"
        yield from self._serialize_model_fields(fields)
        yield "}"

    def _serialize_model_fields(
        self, fields: Iterable[str | _QueryModelType | _QueryOperation]
    ) -> Generator[str, None, None]:
        first = True

        for field in fields:
            if not first:
                yield ","
            first = False

            if isinstance(field, str):
                yield field
            elif isinstance(field, tuple):
                yield from self._serialize_model_query(field)
            elif isinstance(field, _QueryOperation):
                if field.op not in _ALLOWED_FIELD_OPERATIONS:
                    raise ValueError(
                        f"operation `{field.op}` for `{field.model.__name__}` is not allowed in field list query"
                    )
                yield from self._serialize_operation(field)
            else:
                raise TypeError(
                    f"unsupported model field query requested `{field}` of type `{type(field).__name__}`"
                )

    def _serialize_model_or_operation(
        self, model_or_operation: type[BaseModel] | _QueryOperation
    ) -> Generator[str, None, None]:
        if isclass(model_or_operation):
            if issubclass(model_or_operation, BaseModel):
                query_name = getattr(model_or_operation, QL_QUERY_NAME_ATTR, None)
                if query_name is None:
                    raise ValueError(
                        f"couldn't get query name from model `{model_or_operation.__name__}`, are you sure it is a ql model?"
                    )
                yield query_name
            else:
                raise ValueError(
                    f"expected class that ihnerits from `pydantic.BaseModel`, but got `{model_or_operation.__name__}`"
                )
        elif isinstance(model_or_operation, _QueryOperation):
            yield from self._serialize_operation(model_or_operation)
        else:
            raise ValueError(
                f"unknown given class instance in query `{model_or_operation}` of type `{type(model_or_operation).__name__}`"
            )

    def _serialize_operation(
        self, operation: _QueryOperation
    ) -> Generator[str, None, None]:
        if operation.op is _QueryOperationType.INLINE_FRAGMENT:
            __typename__ = getattr(operation.model, QL_TYPENAME_ATTR)
            yield f"...on {__typename__}"
        elif operation.op is _QueryOperationType.ARGUMENTS:
            query_name = getattr(operation.model, QL_QUERY_NAME_ATTR)
            arguments = ",".join(f'{k}:"{v}"' for k, v in operation.extra.items())
            yield f"{query_name}({arguments})"


def arguments(model: type[BaseModel], /, **kwargs) -> _QueryOperation:
    return _QueryOperation(_QueryOperationType.ARGUMENTS, model, kwargs)


def on(model: type[BaseModel]) -> _QueryOperation:
    """when querying model serialize as inline fragment"""
    return _QueryOperation(_QueryOperationType.INLINE_FRAGMENT, model)


def query(*query_models: _QueryModelType, include_typename: bool = True) -> str:
    """
    returns string version of requester query
    """
    return _QuerySerializer(query_models, include_typename).serialize()


def query_response(
    *query_models: _QueryModelType, include_typename: bool = True
) -> dict[Any, Any]:
    """
    converts given query model to string and preform an http request,
    returns the http response

    response = ql.query_response(
        (Point, (
            ql._(Point).x,
            ql._(Point).y
        ))
    )

    --response--
    {"data": "point": {"x": 50, "y": -50}}
    """
    query_string = _QuerySerializer(
        query_models, include_typename=include_typename
    ).serialize()
    return http.request(query_string)
