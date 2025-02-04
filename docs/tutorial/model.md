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

???+ example
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

graphql has the option for interfaces, that different types can implement, thus
we can query an interface but the concrete type is different

---

### `__ql_implements__`
graphql supports interfaces that we can think about it as inheritance in python,
so we define a base class (interface) and we have different types that inherite
from the base class.

the `__ql_implements__` will return list of models that implement the class

???+ example
    <div class="annotate" markdown>
    ```py
    import ql
    from pydantic import BaseModel


    @ql.model
    class Human(BaseModel):
        first_name: str
        last_name: str


    @ql.model
    class Male(Human):
        pass


    @ql.model
    class Female(Human):
        pregnant: bool

    # -- (1)
    assert ql.implements(Human) == (Male, Female)
    ```
    </div>

    1. [api documentation for `implements`](../api/model.md#implements)

---

### `__ql_query_fields_enum__`
this attribute is an enum, the keys are the configured
field names, the value is the configured query name with `ql.metadata`

???+ example
    <div class="annotate" markdown>
    ```py
    class ql
    from typing import Annotated
    from pydantic import BaseModel


    @ql.model
    class Foo(BaseModel):
      something: Annotated[str, ql.metadata(query_name="different")]  # -- (1)


    @ql.model
    class Foo2(BaseModel):
      another: str

    # -- (2)
    assert ql.model_queryable_fields(Foo).something.value == "different"
    assert ql._(Foo).something.value == "different"
    assert ql._(Foo2).another.value == "another"
    ```
    </div>

    1. notice that we change the `query_name`
    2. a safe way to get the information; for api information [click here](../api/model.md#ql.queryable_fields)
