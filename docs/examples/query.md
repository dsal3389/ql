# Query
querying should be expected and simple

## raw query
```py
import ql
import requests

def graphql_request(query: str) -> dict:
  response = requests.post("...", json={"query": query})
  response.raise_status_code()
  return response.json()

ql.http.set_request_func(graphql_request)

graphql_response = ql.raw_query_response("""
  query {
    Person {
      name
      age
    }
  }
""")
```

## raw query scalar response
```py
import ql
import requests
from pydantic import BaseModel

def graphql_request(query: str) -> dict:
  response = requests.post("...", json={"query": query})
  response.raise_status_code()
  return response.json()

ql.http.set_request_func(graphql_request)

@ql.model
class Point(BaseModel):
  x: int
  y: int

query_response = ql.raw_query_response_scalar("""
  query {
    Point {
      x
      y
      __typename
    }
  }
""")
# {"point": [Point(x=5, y=5), Point(x=0, y=-5)]}
```

## python query structure to string
```py
import ql
from pydantic import BaseModel


@ql.model
class Human(BaseModel):
  name: str
  age: int


@ql.model
class Female(Human):
  is_pregnant: bool


@ql.model
class Male(Human):
  working: bool


query_str = ql.query(
  (Human, (
    ql._(Human).name,
    ql._(Human).age
  )),
)
# query{Human{name,age,__typename}}


query_str2 = ql.query(
  (Human, (
    ql._(Human).name,
    (ql.on(Female), (
      ql._(Female).is_pregnant,
    )),
    (ql.on(Male), (
      ql._(Male).working,
    )),
  ))
)
# query{Human{name,...on Female{is_pregnant,__typename},...on Male{working,__typename},__typename}}
```

