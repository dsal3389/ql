# ql (in development)
Graphql client library, wrapped around pydantic classes for type validation,
provide simple, safe and pythonic way to query data from a graphql api.


using pydantic for creating python objects from rest api is common, it is easy and 
it has type validation, so why not make it easy also for graphql apis?

features:
  * python objects to valid graphql string
  * http send and recv information
  * scalar query responses



## TOC
 * [install](#install)
 * [what can it do](#what-can-it-do)
 * [how does it handle http](#how-does-it-handle-http)
 * [configure my pydantic model](#configure-my-pydantic-model)
 * [querying](#querying)
    * [what if my class name is different from my query name?](#what-if-my-class-name-is-different-from-my-query-name)
    * [what if my field name is different from my query name?](#what-if-my-field-name-is-different-from-my-query-name)
 * [query operations](#query-operations)
    * [arguments](#arguemnts)
    * [inline fragments](#inline-fragments)
 * [http](#http)
 * [query examples](#query-examples)
    * [simple query](#simple-query)
    * [smart implements w nested query w inline fragment](#smart-implements-w-nested-query-w-inline-fragment)
    * [query with http](#query-with-http)
    * [query and scalar response](#query-and-scalar-response)
 * [api](#api)
    * [model](#model)
      * [query_fields_nt](#query_fields_nt)
    * [query](#query)


## install
```
pip3 install pydantic-graphql
```

## what can it do
at the time of writing, the `ql` library supports only querying data and scalarazing it to 
the pydantic models, no extra code is required to make your pydantic model compatible
with the library.

to get a better image you can take a look at the [#query examples](#query-examples)

## how does it handle http?
http can be different from implementation to implementation, most implementation of graphql
are very simple, a single `POST` request with `basic authentication`, there is no need for that
to be controlled by the library, the whole point of this library is to make it easy to work
with `pydantic` and graphql apis, for how configure http read [#http](#http)

## configure my pydantic model
it is simple, you can just configure your pydantic model like so

```py
import ql
from pydantic import BaseModel

@ql.model
class MyModel(BaseModel):
  ...
```

# querying
querying is the most common operation in any api, we read data more then
we mutate it, we will use this simple model for our example
```py
import ql
from pydantic import BaseModel

@ql.model
class Point(BaseModel):
  x: int
  y: int
```

if we want to query this model from graphql, our request probably will look like this 
```gql
query {
  Point {
    x,
    y
  }
}
```
with the `ql` library it will look like so
```py
import ql 

# define the `Point` model

query_str = ql.query(
  (Point, (
    ql._(Point).x,
    ql._(Point).y
  ))
)
```
> what the heck is the `_` function? read here [about the function](#query_fields_nt)

this python code will convert the python tuple to a valid graphql query that we 
can use to send graphql, we can print it 
```py
print(query_str)
# query{Point{x,y,__typename}}
```
by default, all `query` functions will add the `__typename` field, we can prevent that
with passing the `query` function argument `include_typename=False`, but we won't do that for now.

the basic structure of a python query tuple is this
```
(<model>, (
  <field_a>,
  <field_b>,
  ...
))
```

now how do you deal with nested models? 
```py
import ql
from pydantic import BaseModel

@ql.model
class Owner(BaseModel):
  name: str
  age: int

@ql.model
class Shop(BaseModel):
  owner: Owner
  items_count: int
```
we want to query shop with the owner data, our graphql query will look like so
```gql
query {
  Shop {
    items_count,
    owner {
      name
      age
    }
  }
}
```
our python query will look like so
```py
query_str = ql.query(
  (Shop, (
    ql._(Shop).items_count,
    (ql._(owner), (
      ql._(Owner).name,
      ql._(Owner).age
    ))
  ))
)
```
you see the pattern? for sub fields we use the same structured tuple,
but instead of a model, we give it a field, it this nesting can continue as
much as we want.
```
(<model>, (
  <field_a>,
  <field_b>,
  (<field_c>, (
    <c_model_field_a>,
    <c_model_field_b>
    ...
  ))
))
```

#### what if my class name is different from my query name?
by default when you decorate your model with `ql.model`, the used 
name in the query is the class name, but lets say we have this case
```py
import ql
from pydantic import BaseModel

@ql.model
class Human(BaseModel):
  name: str
```
but our query should look like this
```gql
query {
  person {    # we need the name `person` instead of human
    name
  }
}
```
for that `ql.model` can take the argument `query_name` which will be used
when we query that model
```py
@ql.model(query_name="person")
class Human(BaseModel):
  ...
```
and we can query regularlly
```py
query_str = ql.query(
  (Human, (
    ql._(Human).name
  ))
)
print(query_str)
# query{person{name, __typename}}
```

#### what if my field name is different from my query name?
in case we have this case:
```py
import ql
from pydantic import BaseModel

@ql.model
class Human(BaseModel):
  first_name: str
  middle_name: str
  last_name: str
```
but our query should look like so
```gql
query {
  Human {
    name,  # first_name
    middle,  # middle_name
    last  # last_name
  }
}
```
we can attach metadata to our field that tells `ql`, that this field
has different query name
```py
...
from typing import Annotated

@ql.model
class Human(BaseModel):
  first_name: Annotated[str, ql.metadata(query_name="first")]
  middle_name: Annotated[str, ql.metadata(query_name="middle")]
  last_name: Annotated[str, ql.metadata(query_name="last")]
```
we can query regularly and we get our expected results
```py
query_str = ql.query(
  (Human, (
    ql._(Human).first_name,
    ql._(Human).middle_name,
    ql._(Human).last_name
  ))
)
print(query_str)
# query{Human{first,middle,last,__typename}}
```

# query operations
in graphql we have couple of operations that we can use
when we query our data

#### raw query
send a simple query string and get response dict
```py
response = ql.raw_query_response("""
  query {
    Person(name: "bob") {
      name,
      age
    }
  }
""")
```

#### scalar response
scalar given graphql response, note that the response
must contain the `__typename` field for any type, thats how the scalar
knows which model should be used

#### arguments
graphql supports [arguments](https://graphql.org/learn/queries/#arguments) when querying, `ql` supports
it too
```py
import ql
from pydantic import BaseModel

@ql.model
class Human(BaseModel):
  name: str
  age: int

query_str = ql.query(
  (ql.arguments(Human, filter="age <= 50"), (
    ql._(Human).name,
    ql._(Human).age
  ))
)
print(query_str)
# query{Human(filter: "age <= 50"){name,age,__typename}}
```
it is simple as just wrapping our model with `ql.arguments`

#### inline fragments
graphql supports [inline fragments](https://graphql.org/learn/queries/#inline-fragments), this happens when a type can return multiple
different types with different fields, `ql` supports that too
```py
import ql
from pydantic import BaseModel

@ql.model
class Human(BaseModel):
  name: str

@ql.model
class Male(Human):
  working: bool

@ql.model
class Female(Human):
  pregnant: bool

query_str = ql.query(
  (Human, (
    ql._(Human).name,
    (ql.on(Male), (
      ql._(Male).working,
    )),
    (ql.on(Female), (
      ql._(Female).pregnant,
    ))
  ))
)
print(query_str)
# query{Human{name, ...on Male{working,__typename}, ...on Female{pregnant,__typename},__typename}}
```

# http
todo

# Query examples
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

#### smart implements w nested query w inline fragment
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

# api

## model
### query_fields_nt
returns a namedtuple with the model `queryable` fields, which maps between
the model field name, to the defined field `query_name`.

```py
import ql 
from typing import Annotated
from pydantic import BaseModel

@ql.model
class Human(BaseMode):
  first_name: Annotated[str, ql.metadata(query_name="name")]
  last_name: Annotated[str, ql.metadata(query_name="family_name")]
  age: int

print(ql.query_fields_nt(Human).first_name)  # name
print(ql.query_fields_nt(Human).last_name)   # family_name
print(ql.query_fields_nt(Human).age)  # age
```
> NOTE: because this function is common when querying, there is a function alias `_`
> which just wraps the `query_fields_nt`, so calling `_` is actually calling `query_fields_nt`

## query
### query
todo

### query_response
todo

### query_response_scalar
