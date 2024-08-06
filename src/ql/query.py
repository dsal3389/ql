from typing import Generator, TypeAlias
from pydantic import BaseModel

from ._const import QL_QUERY_NAME_ATTR


_QueryModelsType: TypeAlias = tuple[BaseModel, tuple["str | _QueryModelsType", ...]]


class _QuerySerializer:
    def __init__(self, query_models: tuple[_QueryModelsType, ...]) -> None:
        self._query = query_models

    def serialize(self) -> str:
        return "".join(self._serialize_query())

    def _serialize_query(self) -> Generator[str, None, None]:
        yield "query{"
        for model_query in self._query:
            yield from self._serialize_model_query(model_query)
        yield "}"

    def _serialize_model_query(
        self, model_query: _QueryModelsType
    ) -> Generator[str, None, None]:
        model, fields = model_query
        model_query_name = getattr(model, QL_QUERY_NAME_ATTR, None)

        if model_query_name is None:
            raise ValueError(
                f"given model `{model.__name__}` missing ql query name attribute, are you sure it is a `ql` model?"
            )

        yield model_query_name
        yield "{"
        yield from self._serialize_model_fields(fields)
        yield "}"

    def _serialize_model_fields(
        self, fields: tuple[str | _QueryModelsType, ...]
    ) -> Generator[str, None, None]:
        first = True

        for field in fields:
            if not first:
                yield ","
            else:
                first = False

            if isinstance(field, str):
                yield field
            elif isinstance(field, tuple):
                yield from self._serialize_model_query(field)
            else:
                raise TypeError(
                    f"unsupported model field query requested `{field}` of type `{type(field).__name__}`"
                )


def arguments(model: type[BaseModel], /, **kwargs) -> tuple[type[BaseModel], str]:
    args = ",".join(f"{k} = '{v}'" for k, v in kwargs.items())
    return (model, args)


def query(*query_models: _QueryModelsType) -> str:
    """
    returns string version of requester query
    """
    return _QuerySerializer(query_models).serialize()
