from __future__ import annotations

import enum
from inspect import isclass
from itertools import chain
from typing import TypeAlias, Any
from typing_extensions import Self
from collections.abc import Generator, Iterable
from pydantic import BaseModel

from ._http import http
from ._const import QL_QUERY_NAME_ATTR, QL_TYPENAME_ATTR
from ._model import typename, all_models, model_queryable_fields
from ._exceptions import QLErrorResponseException
from ._typing import QueryResponseDict
from ._types import QLModel


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
        model: type[QLModel],
        extra: dict[Any, Any] = {},
    ) -> None:
        if not issubclass(model, BaseModel):
            raise TypeError(
                f"given model for operation `{op}` function does not inhertie from `pydantic.BaseModel`, model: `{model}`"
            )
        self.op = op
        self.model = model
        self.extra = extra


QueryKeyTypes: TypeAlias = type[QLModel] | _QueryOperation | str | enum.Enum
QueryFieldTypes: TypeAlias = "str | enum.Enum | QueryRequestSchema | _QueryOperation"

QueryRequestSchema: TypeAlias = tuple[
    QueryKeyTypes,
    Iterable[QueryFieldTypes],
]
QueryFragmentSchema: TypeAlias = tuple[
    tuple[str, QLModel], Iterable["QueryFieldTypes | QueryRequestSchema"]
]


class _QuerySerializer:
    __slots__ = ("_query", "_fragments", "_include_typename")

    def __init__(
        self,
        query_models: Iterable[QueryRequestSchema],
        fragments: Iterable[QueryFragmentSchema] | None,
        include_typename: bool,
    ) -> None:
        self._query = query_models
        self._fragments = fragments
        self._include_typename = include_typename

    def serialize(self) -> str:
        return "".join(self._serialize_query())

    def _serialize_query(self) -> Generator[str, None, None]:
        yield "{"
        for model_query in self._query:
            yield from self._serialize_model_query(model_query)

        if self._fragments:
            for fragment_data, fragment_query in self._fragments:
                name, model = fragment_data
                if (typename_ := typename(model)) is None:
                    raise ValueError(
                        f"couldn't get model typename for fragment `{name}`, are you sure `{model.__name__}` is a ql model?"
                    )

                yield f"fragment {name} on {typename_}"
                yield from self._serialize_model_fields(fragment_query)
        yield "}"

    def _serialize_model_query(
        self, model_query: QueryRequestSchema
    ) -> Generator[str, None, None]:
        """
        takes a model query which constructed of a tuple with 2 value,
        the model class and the query fields, the model can be wrapped in graphql
        operation like `fragment` or `on`
        """
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
        self, fields: Iterable[QueryFieldTypes]
    ) -> Generator[str, None, None]:
        """serialize query model fields"""
        first = True

        for field in fields:
            if not first:
                yield ","
            first = False

            if isinstance(field, enum.Enum):
                yield field.name
            elif isinstance(field, str):
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
        self, model_or_operation: QueryKeyTypes
    ) -> Generator[str, None, None]:
        """
        takes the model from the query tuple, the model can be wrapped in
        some graphql operation
        """
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
        elif isinstance(model_or_operation, enum.Enum):
            yield model_or_operation.name
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

    def scalar(self) -> dict[str, QLModel | list[QLModel]]:
        errors = self._query_response.get("errors")

        if errors is not None:
            raise QLErrorResponseException(errors)

        data = self._query_response["data"]
        return self._scalar_from_models_dict(data)  # type: ignore

    def _scalar_from_models_dict(
        self, dict_: dict[Any, Any]
    ) -> dict[str, QLModel | list[QLModel]]:
        scalared: dict[str, QLModel | list[QLModel]] = {}

        for model_key_name, values in dict_.items():
            if isinstance(values, dict):
                scalared[model_key_name] = self._scalar_dict(values)  # type: ignore
            elif isinstance(values, list):
                scalared[model_key_name] = []
                for value in values:
                    scalared[model_key_name].append(self._scalar_dict(value))  # type: ignore
            else:
                scalared[model_key_name] = values
        return scalared

    def _scalar_dict(self, dict_: dict[str, Any]) -> BaseModel:
        """
        takes a dictionary, which represent a model instance, every nested dict
        is treated as a sub model, initlize the mode and the sub models if possible
        by using the `__typename` field
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

        scalared_fields: dict[str, Any] = {}

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
        self, model: type[QLModel], fields: dict[str, Any]
    ) -> QLModel:
        """
        create a new instance of the model with respect to the model's field metadata,
        it is expected that field that expect models (sub model) will already be initilized,
        and not relay on `pydantic` for it
        """
        queryable_fields_enum = model_queryable_fields(model)
        query_name_to_model_name = {
            variant.value: variant.name for variant in list(queryable_fields_enum)
        }

        model_init_kwargs = {}

        for field_name, value in fields.items():
            if field_name in query_name_to_model_name:
                field_name = query_name_to_model_name[field_name]
            model_init_kwargs[field_name] = value
        return model(**model_init_kwargs)


class QueryModelBuilder:
    def __init__(self, model: str | enum.Enum | type[QLModel]) -> None:
        self._model = model
        self._fields: list[QueryFieldTypes] = []

    def fields(self, *fields: QueryFieldTypes | QueryModelBuilder) -> Self:
        for field in fields:
            if isinstance(field, QueryModelBuilder):
                self._fields.append(field.build())
            else:
                self._fields.append(field)
        return self

    def build(self) -> QueryRequestSchema:
        assert (
            self._fields is not None
        ), "cannot build model query, no fields were added"
        return (self._model, self._fields)


class QueryFragmentBuilder(QueryModelBuilder):
    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._name = name

    def build(self) -> QueryFragmentSchema:  # type: ignore
        assert (
            self._fields is not None
        ), "cannot build fragment query, no fields were added"
        return (fragment(self._name, self._model), self._fields)  # type: ignore


class QueryBuilder:
    def __init__(self, *, include_typename: bool = True) -> None:
        self._include_typename = include_typename
        self._query_models: list[QueryRequestSchema] = []
        self._fragments: list[QueryFragmentSchema] = []

    def model(self, model_builder: QueryModelBuilder) -> Self:
        self._query_models.append(model_builder.build())
        return self

    def fragment(self, fragment_builder: QueryFragmentBuilder) -> Self:
        self._fragments.append(fragment_builder.build())
        return self

    def build(self) -> str:
        """returns the built query as valid graphql string"""
        return _QuerySerializer(
            query_models=self._query_models,
            fragments=self._fragments,
            include_typename=self._include_typename,
        ).serialize()

    def query(self) -> QueryResponseDict:
        """perform a query request and returns the response"""
        return query_response(
            *self._query_models,
            fragments=self._fragments,
            include_typename=self._include_typename,
        )

    def scalar(self) -> dict[str, QLModel | list[QLModel]]:
        """performs a query request and scalar the response"""
        return query_response_scalar(
            *self._query_models,
            fragments=self._fragments,
        )


def arguments(model: type[QLModel], /, **kwargs) -> _QueryOperation:
    return _QueryOperation(_QueryOperationType.ARGUMENTS, model, kwargs)


def on(model: type[QLModel]) -> _QueryOperation:
    """when querying model serialize as inline fragment"""
    return _QueryOperation(_QueryOperationType.INLINE_FRAGMENT, model)


def fragment_ref(name: str) -> _QueryOperation:
    """reference defined fragment"""
    return _QueryOperation(
        _QueryOperationType.REFERENCE_FRAGMENT, _Placeholder, {"fragment_name": name}
    )


def fragment(name: str, model: type[QLModel]) -> tuple[str, type[QLModel]]:
    """
    used for setting a fragment for when calling a query function and passing the `fragments`
    arguments.
    """
    return (name, model)


def raw_query_response(query_str: str) -> QueryResponseDict:
    """return the http response for given query string"""
    return http.request(query_str)


def raw_query_response_scalar(query_str) -> dict[str, QLModel | list[QLModel]]:
    """sends the given query string with http, but scalarizie the response"""
    response = http.request(query_str)
    return _QueryResponseScalar(response).scalar()


def scalar_query_response(
    query_reponse: QueryResponseDict,
) -> dict[str, QLModel | list[QLModel]]:
    """
    scalar a graphql query response with models defined with `ql.model`
    """
    return _QueryResponseScalar(query_reponse).scalar()


def query(
    *query_models: QueryRequestSchema,
    fragments: Iterable[QueryFragmentSchema] | None = None,
    include_typename: bool = True,
) -> str:
    """
    returns string version of requester query
    """
    return _QuerySerializer(
        query_models, fragments=fragments, include_typename=include_typename
    ).serialize()


def query_response(
    *query_models: QueryRequestSchema,
    fragments: Iterable[QueryFragmentSchema] | None = None,
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
        query_models, fragments=fragments, include_typename=include_typename
    ).serialize()
    return http.request(query_string)


def query_response_scalar(
    *query_models: QueryRequestSchema,
    fragments: Iterable[QueryFragmentSchema] | None = None,
) -> dict[str, QLModel | list[QLModel]]:
    response = query_response(*query_models, fragments=fragments, include_typename=True)
    return scalar_query_response(response)
