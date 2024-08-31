# model

## ql.all_models
returns a dict mapping between all registered models and thier 
registered typename

```py
def all_models() -> dict[str, type[BaseModel]]:
```

## ql.typename
returns the model configured typename, if model is not registered
with `ql.model` then return `None`

```py
def typename(model: type[BaseModel]) -> Optional[str]:
```

| Name | Type | Description |
|------|------|-------------|
| `model` | `type[BaseModel]` | the model we want the typename for |


## ql.implements
returns all child models, that the given model implements

```py
def implements(cls: type[BaseModel]) -> tuple
```

| Name | Type | Description |
|------|------|-------------|
| `cls` | `type[BaseModel]` | the model we want to take implementations from |

```py
import ql
from pydantic import BaseModel


@lq.model
class Human(BaseModel):
    first_name: str
    last_name: str


@ql.model
class Male(Human):
    pass


@ql.model
class Female(Human):
    pass


print(ql.implements(Human))
# (<class '__main__.Male'>, <class '__main__.Female'>)
```

## ql.query_fields_nt
returns a namedtuple of all queryable fields in the given model, mapping between
the model field name to the query name.

!!! info
    this function is also aliased as `ql._` because it is common

```py
def query_fields_nt(cls: type[BaseModel]) -> Any
```

| Name | Type | Description |
|------|------|-------------|
| `cls` | `type[BaseModel]` | the model we want the namedtuple from |

```py
import ql
from typing import Annotated
from pydantic import BaseModel


@ql.model
class Article(BaseModel):
    name: Annotated[str, ql.metadata(query_name="title")]
    description: str

    foo: Annotated[str, ql.metadata(queryable=False)]

print(ql.query_fields_nt(Article).name)         # "title"
print(ql.query_fields_nt(Article).description)  # "description"
print(ql.query_fields_nt(Article).foo)          # exception

```
