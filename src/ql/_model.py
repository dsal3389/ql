from collections import namedtuple
from typing import Callable, Optional, Any
from pydantic import BaseModel

from ._const import (
    QL_MUTATE_NAME_ATTR,
    QL_QUERY_NAME_ATTR,
    QL_IMPLEMENTS_ATTR,
    QL_QUERYABLE_FIELDS_NT_ATTR,
    QL_MUTABLE_FIELDS_NT_ATTR,
    QL_TYPENAME_ATTR,
)
from ._typing import QLFieldMetadata


_ALL_REGISTERD_MODELS: dict[str, type[BaseModel]] = {}


def all_models() -> dict[str, type[BaseModel]]:
    """returns a tuple of all registered models"""
    return _ALL_REGISTERD_MODELS.copy()


def typename(model: type[BaseModel]) -> Optional[str]:
    """returns the model typename"""
    return getattr(model, QL_TYPENAME_ATTR, None)


def implements(cls: type[BaseModel]) -> tuple:
    """returns the model implemention list"""
    implements = getattr(cls, QL_IMPLEMENTS_ATTR, {})
    return tuple(implements.values())


def query_fields_nt(cls: type[BaseModel]) -> Any:
    """
    returns the model queryable namedtuple fields, mapping between model field name to the
    query name value
    """
    return getattr(cls, QL_QUERYABLE_FIELDS_NT_ATTR)


def mutate_fields_nt(cls: type[BaseModel]) -> Any:
    """
    returns the model mutable namedtuple fields, mapping between model field name to the
    mutate name value
    """
    return getattr(cls, QL_MUTABLE_FIELDS_NT_ATTR)


def _process_model(
    cls: type[BaseModel],
    typename: Optional[str],
    query_name: Optional[str],
    mutate_name: Optional[str],
) -> type[BaseModel]:
    if not issubclass(cls, BaseModel):
        raise TypeError(
            f"given class `{cls.__name__}` does not inherits from `pydantic.BaseModel`"
        )

    typename = typename or cls.__name__

    # set minimum required attributes
    setattr(cls, QL_QUERY_NAME_ATTR, query_name or cls.__name__)
    setattr(cls, QL_MUTATE_NAME_ATTR, mutate_name or cls.__name__)
    setattr(cls, QL_TYPENAME_ATTR, typename)
    setattr(cls, QL_IMPLEMENTS_ATTR, {})

    for mro in cls.__mro__[1:]:
        # if mro is not a `BaseModel` and it doesn't have `QL_IMPLEMENTS_ATTR`
        # then its not a graphql model
        if not issubclass(mro, BaseModel) or not hasattr(mro, QL_IMPLEMENTS_ATTR):
            continue

        # add current class to parent
        # classes because they implement the current one
        __implements__ = getattr(mro, QL_IMPLEMENTS_ATTR)
        __implements__[typename] = cls

    queryable_fields: list[tuple[str, str]] = []
    mutable_fields: list[tuple[str, str]] = []

    for name, field_info in cls.model_fields.items():
        ql_field_metadata: Optional[QLFieldMetadata] = None

        for metadata in field_info.metadata:
            if isinstance(metadata, QLFieldMetadata):
                ql_field_metadata = metadata
                break

        if ql_field_metadata is None:
            ql_field_metadata = QLFieldMetadata(
                query_name=name,
                mutate_name=name,
            )
        if ql_field_metadata.queryable:
            queryable_fields.append((name, ql_field_metadata.query_name or name))
        if ql_field_metadata.mutable:
            mutable_fields.append((name, ql_field_metadata.mutate_name or name))

    # namedtuples that map between the field name to the field `query_name`/`mutate_name`
    # it is a namedtuple, so it will be dot access, type ignore because `mypy`
    # doesn't support namedtuples with dynamic fields
    QueryFields = namedtuple("QueryFields", (qf[0] for qf in queryable_fields))  # type: ignore
    MutateFields = namedtuple("MutateFields", (mf[0] for mf in mutable_fields))  # type: ignore

    setattr(
        cls,
        QL_QUERYABLE_FIELDS_NT_ATTR,
        QueryFields(*(qf[1] for qf in queryable_fields)),
    )
    setattr(
        cls,
        QL_MUTABLE_FIELDS_NT_ATTR,
        MutateFields(*(mf[1] for mf in mutable_fields)),
    )

    # register the model to the list
    _ALL_REGISTERD_MODELS[typename] = cls
    return cls


def model(
    cls: Optional[type[BaseModel]] = None,
    /,
    *,
    typename: Optional[str] = None,
    query_name: Optional[str] = None,
    mutate_name: Optional[str] = None,
) -> type[BaseModel] | Callable[..., type[BaseModel]]:
    """
    defines the given pydantic class as a ql model, setting `__ql_<...>__`
    attributes that are used accross the ql library to execute required operations

    @ql.model
    class Person(BaseModel):
        name: str
        age: int

    if our pydantic class inherits from different `model`, the class will be automatically
    added to the `implements` list of the parent class

    @ql.model
    class Human(BaseModel):
        ...

    @ql.model
    class Female(Human):
        ...

    @ql.model
    class Male(Human):
        ...

    ql.implements(Human)  # we will see `Female` and `Male`
    """

    def _process_model_proxy(cls: type[BaseModel]) -> type[BaseModel]:
        return _process_model(cls, typename, query_name, mutate_name)

    if cls is not None:
        return _process_model_proxy(cls)
    return _process_model_proxy  # type: ignore
