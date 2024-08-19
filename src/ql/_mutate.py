from typing import Generator, Any, Optional, Iterable
from pydantic import BaseModel

from ._const import QL_MUTATE_NAME_ATTR, QL_MUTABLE_FIELDS_NT_ATTR
from ._query import _QueryModelType, query


class _MutateSerializer:
    __slots__ = ("_name", "_data", "_return_query")

    def __init__(self, name: str, data: dict, return_query: str) -> None:
        self._name = name
        self._data = data
        self._return_query = return_query

    def serialize(self) -> str:
        return "".join(self._serialize_mutate_dict())

    def _serialize_mutate_dict(self) -> Generator[str, None, None]:
        yield "mutate{"
        yield self._name
        yield "("
        yield from self._serialize_dict(self._data)
        yield ")"
        yield self._return_query
        yield "}"

    def _serialize_dict(self, dict_: dict) -> Generator[str, None, None]:
        first = True
        for key, value in dict_.items():
            if not first:
                yield ","
            first = False

            yield from self._serialize_dict_key(key)
            yield ":"
            yield from self._serialize_dict_value(value)

    def _serialize_dict_key(self, key: Any) -> Generator[str, None, None]:
        if isinstance(key, str):
            yield key
        else:
            raise ValueError(f"dict key cannot be of value `{type(key).__name__}`")

    def _serialize_dict_value(self, value: Any) -> Generator[str, None, None]:
        if isinstance(value, str):
            yield f'"{value}"'
        elif isinstance(value, int):
            yield str(value)
        elif isinstance(value, bool):
            yield str(value).lower()
        elif isinstance(value, dict):
            yield "{"
            yield from self._serialize_dict(value)
            yield "}"
        else:
            raise ValueError(
                f"couldn't serialize dict value of type `{type(value).__name__}`"
            )


class _ModelToMutateDictSerializer:
    """
    converts given model instance to a dict with respect
    to the defined metadata in the model fields
    """

    __slots__ = ("_model", "_include_fields", "_exclude_fields")

    def __init__(
        self,
        model: BaseModel,
        include_fields: set[str],
        exclude_fields: set[str],
    ) -> None:
        self._model = model
        self._include_fields = include_fields
        self._exclude_fields = exclude_fields

        if self._exclude_fields and self._include_fields:
            raise ValueError(
                "cannot set `exclude_fields` and `include_fields` together"
            )

    def serialize(self) -> dict:
        return self._serialize_model(self._model)

    def _serialize_model(self, model: BaseModel) -> dict:
        mutable_fields = getattr(model, QL_MUTABLE_FIELDS_NT_ATTR, None)
        if mutable_fields is None:
            raise ValueError(f"Couldn't mutable fields for model `{model.__name__}`.")

        serialized = {}
        for field_name, field_mutate_name in mutable_fields._asdict().items():
            if field_name in self._exclude_fields:
                continue

            field_value = getattr(model, field_name)
            serialized[field_mutate_name] = field_value
        return serialized


def mutate(
    model: BaseModel,
    return_query: _QueryModelType,
    *,
    include_typename: bool = True,
    include_fields: Optional[set[str]] = None,
    exclude_fields: Optional[set[str]] = None,
) -> str:
    mutate_name = getattr(model, QL_MUTATE_NAME_ATTR, None)
    if mutate_name is None:
        raise ValueError(
            f"given model `{model.__name__}` to mutate doesn't have mutate name defined, is it `@ql.model`?"
        )

    asdict = _ModelToMutateDictSerializer(
        model,
        include_fields=include_fields or set(),
        exclude_fields=exclude_fields or set(),
    ).serialize()
    return_query_str = query(return_query, include_typename=include_typename)
    return _MutateSerializer(mutate_name, asdict, return_query_str).serialize()
