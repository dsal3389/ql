# ql (in development)
Graphql client library, wrapped around pydantic classes for typing validation,
provide simple, safe and dynamic way to query data from a graphql api.


using pydantic for creating python objects from rest api is common, it is easy and 
it has type validation, so why not do that also for graphql apis?

features:
  * python objects to valid graphql string
  * http send and recv information
  * scalar http responses

## Query examples
#### simple query
> ```py
> import ql
> from pydantic import BaseModel
> 
> 
> @ql.model
> class Point(BaseModel):
>   x: int
>   y: int
> 
> 
> q = ql.query(
>   (Point, (
>     ql._(Point).x,
>     ql._(Point).y
>   ))
> )
> print(q)
> ```
> ---
> ```
> query{Point{x,y}}
> ```

#### different query names then what defined
> ```py
> import ql
> from pydantic import BaseModel, Field
> 
> 
> @ql.model(query_name="Person")
> class Adult(BaseModel):
>   name: Annotation[str, ql.metadata(query_name="first_name")]
>
> q = ql.query((Adult,(ql._(Adult).name,))
> print(q)
> ```
> ---
> ```
> query{Person{first_name}}
> ```

#### smart implements + nested query + inline fragment
> ```py
> import ql
> from pydantic import BaseModel
>
> @ql.model
> class Human(BaseModel):
>   first_name: str
>   last_name: str
>
> @ql.model
> class Female(Human):
>   pregnant: bool
>
> @ql.model
> class Male(Human):
>   pass
>
> print(ql.implements(Human))  # what does `Human` implement
> q = ql.query(
>     (Human, (
>         ql._(Human).first_name,
>         (ql.on(Female), (
>             ql._(Female).pregnant,
>         ))
>     ))
> )
> print(q)
> ```
> ---
> ```
> frozenset({<class '__main__.Human'>})
> query{Human{first_name,...on Female{pregnant,__typename},__typename}}
> ```

#### query with http
> ```py
> import ql
> import requests
> from pydantic import BaseModel
>
> ql.http.set_request_func(lambda q: requests.get(...).json())
>
> # define models ...
>
> response = ql.query_response(
>   (Point, (
>      ql._(Point).x,
>      ql._(Point).y
>   ))
> )
> print(response)
> ```
> ---
> ```
> {"data": {"point": "x": 50, "y": -50}}
> ```

#### query and scalar response
> ```py
> import ql
> import requests
> from pydantic import BaseModel
>
> ql.http.set_request_func(lambda q: requests.get(...).json())
>
> @ql.model
> class Point(BaseModel):
>   x: int
>   y: int
>
> scalared = ql.query_response_scalar(
>  (Point, (
>    ql._(Point).x,
>    ql._(Point).y
>   ))
> )
> print(scalared)
> ```
> ---
> ```
> {"point": Point(x=50, y=-50)}
> ```
