# query
querying is the most common operation, `ql` provides couple of ways to query
your data.

## raw query
raw querying just accepts your query string, as is, query functions
that accept raw query, are usally prefixed with `raw_`

```py title="example"
import ql

response = ql.raw_query_response("""
query {
    people {
        name
        age
    }
}
""")
```

## query python schema
`ql` also can takes a tuple of 2 values, value at index `0` is the model type, 
value at index `1` is the fields we want to take from the model.

```
(<model>, (
    field, 
    field, 
    field, 
    ...
))
```

in code the query schema will look something like this
```py
import ql
from pydantic import BaseModel


@ql.model
class Person(BaseModel):
    name: str
    age: int


query_str = ql.query(
    (Person, (
        ql._(Person).name,
        ql._(Person).age
    ))
)
```

!!! info "the `ql._` function"
    we wrap the model `Person` inside `ql._` to get the correct field queryname, more information
    about this function [click here](../api/model.md#qlquery_fields_nt)

**NOTICE** that the `query` function and all other query functions that accept python query schema takes 
tuple, and the can take multiple tuples to query multiple graphql types

```py
query_str = ql.query(
    (ModelA, (
        ql._(ModelA).foo,
        ...
    )),
    (ModelB, (
        ql._(ModelB).foo,
        ...
    )),
    ...
)
```

### nested fields
lets first look at an example of querying nested fields
```py
import ql
from pydantic import BaseModel


@ql.model
class Child(BaseModel):
    name: str
    sleeps: bool


@ql.model
class Person(BaseModel):
    name: str
    age: int
    child: Child


query_str = ql.query(
    (Person, (
        ql._(Person).name,
        ql._(Person).age,
        (ql._(Person).child, (
            ql._(Child).name,
            ql._(Child).sleeps
        )),
    ))
)
```

looks a bit more complicated. the nested schema is the same schema as before, but in the nested tuple at index `0`
we don't provide the model, we provide the `ql._(Person).child` field instead.

we can keep nesting like that as much as we want.
```
(<model>, (
    field,
    field, 
    field,
    (field, (
        field,
        field,
        (field, (
            field,
            field,
            ...
        ))
    ))
))
```
