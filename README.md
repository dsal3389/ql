# ql
graphql library for python to create graphql queries with python pydantic objects

```py
import ql
from pydantic import BaseModel


@ql.model
class Point(BaseModel):
  x: int
  y: int


q = ql.query(
  (Point, (
    q._(Point).x,
    q._(Point).y
  ))
)
```

#### different query names then what defined
```py
import ql
from pydantic import BaseModel, Field


@ql.model(query_name="Adult")
class Person(BaseModel):
  name: Annotation[str, ql.metadata(query_name="first_name")]
```
