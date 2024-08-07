import enum
from inspect import isclass
from itertools import chain
from collections.abc import Iterable
from typing import Generator, TypeAlias, Any
from pydantic import BaseModel

from ._const import QL_QUERY_NAME_ATTR, QL_TYPENAME_ATTR, QL_INSTANTIATE
from .model import implements
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
    type[BaseModel] | _QueryOperation | str,
    Iterable["str | _QueryModelType | _QueryOperation"],
]


class _QuerySerializer:
    __slots__ = ("_query", "_include_typename", "_involved_models")

    def __init__(
        self, query_models: tuple[_QueryModelType, ...], include_typename: bool
    ) -> None:
        self._query = query_models
        self._include_typename = include_typename
        self._involved_models = set()

    @property
    def involved_models(self) -> tuple[type[BaseModel]]:
        """
        should be called only after calling `serialize`, this property returns all found models in query
        """
        return tuple(self._involved_models)

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
            elif isinstance(field, (tuple, list, set)):
                yield from self._serialize_model_query(field)
            elif isinstance(field, _QueryOperation):
                if field.op not in _ALLOWED_FIELD_OPERATIONS:
                    raise ValueError(
                        f"operation `{field.op}` for `{field.model.__name__}` is not allowed in field list query"
                    )
                yield from self._serialize_operation(field)
            else:
                raise TypeError(
                    f"expected model on sub model query requested, but got `{field}` of type `{type(field).__name__}`"
                )

    def _serialize_model_or_operation(
        self, model_or_operation: type[BaseModel] | _QueryOperation | str
    ) -> Generator[str, None, None]:
        if isclass(model_or_operation):
            if issubclass(model_or_operation, BaseModel):
                query_name = getattr(model_or_operation, QL_QUERY_NAME_ATTR, None)
                if query_name is None:
                    raise ValueError(
                        f"couldn't get query name from model `{model_or_operation.__name__}`, are you sure it is a ql model?"
                    )
                yield query_name

                if model_or_operation not in self._involved_models:
                    # since we are dealing with a model, we need to add
                    # it to the involve set and the types that model implements
                    self._involved_models.add(model_or_operation)
                    self._involved_models.update(implements(model_or_operation))
            else:
                raise ValueError(
                    f"expected model when querying sub model got `{model_or_operation.__name__}`, does ihnerits from `pydantic.BaseModel`?"
                )
        elif isinstance(model_or_operation, _QueryOperation):
            yield from self._serialize_operation(model_or_operation)
        elif isinstance(model_or_operation, str):
            # if it is a list, it is probably a nested field
            yield model_or_operation
        else:
            raise ValueError(
                f"expected operation or model but got `{model_or_operation}` of type `{type(model_or_operation).__name__}`"
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

        if operation.model not in self._involved_models:
            # add the wrapped operation model
            # to the involved list and the type that model implements
            self._involved_models.add(operation.model)
            self._involved_models.update(implements(operation.model))


class _QueryResponseScalar:
    __slots__ = ("_query_response", "_models", "_typename_to_models")

    def __init__(
        self, query_response: dict[Any, Any], models: Iterable[type[BaseModel]]
    ) -> None:
        self._query_response = query_response
        self._models = models
        self._typename_to_models = {}

        for model in self._models:
            typename = getattr(model, QL_TYPENAME_ATTR)
            self._typename_to_models[typename] = model

    def scalar(self) -> dict[str, BaseModel | list[BaseModel]]:
        data = self._query_response["data"]
        return self._scalar_from_models_dict(data)

    def _scalar_from_models_dict(
        self, dict_: dict[Any, Any]
    ) -> dict[str, BaseModel | list[BaseModel]]:
        scalared = {}

        for model_key_name, values in dict_.items():
            if isinstance(values, dict):
                scalared[model_key_name] = self._scalar_dict(values)
            elif isinstance(values, list):
                scalared[model_key_name] = []
                for value in values:
                    scalared[model_key_name].append(self._scalar_dict(value))
            else:
                scalared[model_key_name] = values
        return scalared

    def _scalar_dict(self, dict_: dict[str, Any]) -> BaseModel:
        """
        takes a dictionary, and for every nested dict, it means it is a model,
        scalar that model to the correct type
        """
        typename = dict_.pop("__typename", None)
        scalar_model = self._typename_to_models.get(typename)

        if scalar_model is None:
            raise ValueError(
                f"couldn't scalar query response, couldn't find required module, typename `{typename}` in requested query"
            )

        scalared_fields = {}

        for key, value in dict_.items():
            if isinstance(value, dict):
                scalared_fields[key] = self._scalar_dict(value)
            elif isinstance(value, list):
                # if it is an empty list or the values inside
                # the list are not nested dicts, then it is some other type
                # that should be not scalared by us
                if len(value) == 0 or not isinstance(value[0], dict):
                    scalared_fields[key] = value
                    continue

                scalared_fields[key] = []
                for sub_dict in value:
                    scalared_fields[key].append(self._scalar_dict(sub_dict))
            else:
                scalared_fields[key] = value
        return scalar_model(**scalared_fields)


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


def query_response_scalar(
    *query_models: _QueryModelType,
) -> dict[str, BaseModel | list[BaseModel]]:
    query_serializer = _QuerySerializer(query_models, include_typename=True)
    query_string = query_serializer.serialize()

    # TODO: handle error responses
    response = http.request(query_string)
    return _QueryResponseScalar(response, query_serializer.involved_models).scalar()
