# Query
reading data from apis is the most common operation we do, that's why `ql` makes it 
easy to query data from your graphql endpoint and provide variety of query methods.


## ql.query
takes python ql query structure and returns a valid graphql query string.
```py
def query(
    *query_models: _QueryModelType,
    fragments: Optional[_QueryFragmentType] = None,
    include_typename: bool = True,
) -> str:
```

| Name | Type | Description |
|------|------|-------------|
| `query_models` |  `*_QueryModelType`          | python ql structured query |
| `fragments` | `Optional[_QueryFragmentType]` | dict mapping between `ql.fragment` to the python ql structured query |
| `include_typename` | `bool` | if include `__typename` field when querying sub types |

```py title="example.py"
import ql
from pydantic import BaseModel

@ql.model
class Point(BaseModel):
  x: int
  y: int

query_str = ql.query(
  (Point, (
    ql._(Point).x,
    ql._(Point).y
  ))
)
```

## ql.query_response
serializes the ql query structure, send it via http and returns the response as `dict`.

```py
def query_response(
    *query_models: _QueryModelType,
    fragments: Optional[_QueryFragmentType] = {},
    include_typename: bool = True,
) -> QueryResponseDict:
```

!!! warning ""
    http request function must be set to make this function work, [click here to view](/api/http).


