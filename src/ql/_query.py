import enum
from inspect import isclass
from itertools import chain
from collections.abc import Iterable
from typing import Generator, Optional, TypeAlias, Any
from pydantic import BaseModel

from ._http import http
from ._const import QL_QUERY_NAME_ATTR, QL_TYPENAME_ATTR
from ._model import typename, all_models, query_fields_nt
from ._exceptions import QLErrorResponseException
from ._typing import QueryResponseDict


class _Placeholder(BaseModel):
    """
    place holder model is used in cases a functions expect to get
    a model but the model is not really required line `fragment_ref`
    """


class _QueryOperationType(enum.Enum):
    ARGUMENTS = enum.auto()
    INLINE_FRAGMENT = enum.auto()
    REFERENCE_FRAGMENT = enum.auto()

    def __str__(self) -> str:
        return self.name


# list of operations that are allowed
# to be defined in query fields
_ALLOWED_FIELD_OPERATIONS = (_QueryOperationType.REFERENCE_FRAGMENT,)

# list of operations that are allowed
# to defined when expecting to get a model
_ALLOWED_MODEL_OPERATIONS = (
    _QueryOperationType.ARGUMENTS,
    _QueryOperationType.INLINE_FRAGMENT,
)


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
_QueryFragmentType: TypeAlias = dict[
    tuple[str, type[BaseModel]], Iterable[str | _QueryModelType | _QueryOperation]
]


class _QuerySerializer:
    __slots__ = ("_query", "_fragments", "_include_typename")

    def __init__(
        self,
        query_models: tuple[_QueryModelType, ...],
        fragments: _QueryFragmentType,
        include_typename: bool,
    ) -> None:
        self._query = query_models
        self._fragments = fragments
        self._include_typename = include_typename

    def serialize(self) -> str:
        return "".join(self._serialize_query())

    def _serialize_query(self) -> Generator[str, None, None]:
        yield "query{"
        for model_query in self._query:
            yield from self._serialize_model_query(model_query)

        for fragment_data, fragment_query in self._fragments.items():
            name, model = fragment_data
            if (typename_ := typename(model)) is None:
                raise ValueError(
                    f"couldn't get model typename for fragment `{name}`, are you sure `{model.__name__}` is a ql model?"
                )

            yield f"fragment {name} on {typename_}"
            yield from self._serialize_model_fields(fragment_query)
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
            else:
                raise ValueError(
                    f"expected model when querying sub model got `{model_or_operation.__name__}`, does ihnerits from `pydantic.BaseModel`?"
                )
        elif isinstance(model_or_operation, _QueryOperation):
            if model_or_operation.op not in _ALLOWED_MODEL_OPERATIONS:
                raise ValueError(
                    f"operation `{model_or_operation.op}` is not allowed when expected a model"
                )
            yield from self._serialize_operation(model_or_operation)
        elif isinstance(model_or_operation, str):
            # if it is a str, it is probably a nested field
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
        elif operation.op is _QueryOperationType.REFERENCE_FRAGMENT:
            yield f"...{operation.extra['fragment_name']}"


class _QueryResponseScalar:
    __slots__ = ("_query_response", "_typename_to_models")

    def __init__(self, query_response: QueryResponseDict) -> None:
        self._query_response = query_response
        self._typename_to_models = all_models()

    def scalar(self) -> dict[str, BaseModel | list[BaseModel]]:
        errors = self._query_response.get("errors")

        if errors is not None:
            raise QLErrorResponseException(errors)

        data = self._query_response["data"]
        return self._scalar_from_models_dict(data)  # type: ignore

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
        if typename is None:
            raise ValueError(
                "couldn't scalar response, expected for sub fields to include the `__typename` field, "
                "make sure you add `__typename` when querying sub types"
            )

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
        return self._instantiate_model(scalar_model, scalared_fields)

    def _instantiate_model(
        self, model: type[BaseModel], fields: dict[str, Any]
    ) -> BaseModel:
        """
        create a new instance of the model with respect to the model's field metadata,
        it is expected that field that expect models will already be initilized,
        and not relay on `pydantic` for it
        """
        queryable_fields = query_fields_nt(model)._asdict()
        query_field_name_to_model_field_name = {
            v: k for k, v in queryable_fields.items()
        }
        model_init_kwargs = {}

        for field_name, value in fields.items():
            if field_name in query_field_name_to_model_field_name:
                model_field_name = query_field_name_to_model_field_name[field_name]
                model_init_kwargs[model_field_name] = value
            else:
                model_init_kwargs[field_name] = value
        return model(**model_init_kwargs)


def arguments(model: type[BaseModel], /, **kwargs) -> _QueryOperation:
    return _QueryOperation(_QueryOperationType.ARGUMENTS, model, kwargs)


def on(model: type[BaseModel]) -> _QueryOperation:
    """when querying model serialize as inline fragment"""
    return _QueryOperation(_QueryOperationType.INLINE_FRAGMENT, model)


def fragment_ref(name: str) -> _QueryOperation:
    """reference defined fragment"""
    return _QueryOperation(
        _QueryOperationType.REFERENCE_FRAGMENT, _Placeholder, {"fragment_name": name}
    )


def fragment(name: str, model: type[BaseModel]) -> tuple[str, type[BaseModel]]:
    """
    used for setting a fragment for when calling a query function and passing the `fragments`
    arguments.
    """
    return (name, model)


def raw_query_response(query_str: str) -> QueryResponseDict:
    """return the http response for given query string"""
    return http.request(query_str)


def raw_query_response_scalar(query_str) -> dict[str, BaseModel | list[BaseModel]]:
    """sends the given query string with http, but scalarizie the response"""
    response = http.request(query_str)
    return _QueryResponseScalar(response).scalar()


def scalar_query_response(
    query_reponse: QueryResponseDict,
) -> dict[str, BaseModel | list[BaseModel]]:
    """
    scalar a graphql query response with models defined with `ql.model`
    """
    return _QueryResponseScalar(query_reponse).scalar()


def query(
    *query_models: _QueryModelType,
    fragments: Optional[_QueryFragmentType] = None,
    include_typename: bool = True,
) -> str:
    """
    returns string version of requester query
    """
    return _QuerySerializer(
        query_models, fragments=fragments or {}, include_typename=include_typename
    ).serialize()


def query_response(
    *query_models: _QueryModelType,
    fragments: Optional[_QueryFragmentType] = {},
    include_typename: bool = True,
) -> QueryResponseDict:
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
        query_models, fragments=fragments or {}, include_typename=include_typename
    ).serialize()
    return http.request(query_string)


def query_response_scalar(
    *query_models: _QueryModelType, fragments: Optional[_QueryFragmentType] = None
) -> dict[str, BaseModel | list[BaseModel]]:
    response = query_response(*query_models, fragments=fragments, include_typename=True)
    return scalar_query_response(response)
