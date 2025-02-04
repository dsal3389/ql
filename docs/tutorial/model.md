# model
modeling your graphql types is done with `pydantic`, and making the model
compatible with the `ql` library, use `lq.model`

## the `@ql.model` and how it works
this decorator defines couple of attributes that are required
for graphql apis and are used across the library.

!!! danger
    **do not** access those properties directly because they
    might be change in the future, the `ql` library provides standard ways
    to access those properties values in a expected manner

---

### `__ql_query_name__`
this property contains the model query name, since we likely
want to query object from graphql with different name then what we defined in python.

the default value is the class name
```py
import ql
from pydantic import BaseModel


@ql.model
class Foo(BaseModel):
    field: str


@ql.model(query_name="different")
class MyClass(BaseModel):
    field: str


assert Foo.__ql_query_name__ == "Foo"
assert MyClass.__ql_query_name__ == "different"

# value is used when querying they model
assert ql.query((Foo, (ql._(Foo).field,))) == "{Foo{field,__typename}}"
assert ql.query((MyClass, (ql._(MyClass).field,))) == "{different{field,__typename}}"
```

---

### `__ql_typename__`
graphql has the builtin-field `__typename` which returns the name of
the returned object.

graphql can implement interfaces that different types implement, we can query

| Name | Type | Description |
|-------|------|-------------|
| `__ql_query_name__` | `str` | the model query name in graphql |
| `__ql_typename__` | `str` | the model `__typename` as it is in the graphql api, this will help us scalar responses |
| `__ql_implements__` | `dict[str, type[BaseModel]]` | inheriting models will register themselves the parents `__ql_implements__` |
| `__ql_query_fields_nt__` | `NamedTuple` | returns a named tuple with all queryable fields, the name tuple maps between the field to the graphql field name based on the `ql.metadata` attached to the field |
