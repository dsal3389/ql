# query
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
| `query_models` | `*_QueryModelType` | python ql structured query |
| `fragments` | `Optional[_QueryFragmentType]` | dict mapping between `ql.fragment` to the python ql structured query |
| `include_typename` | `bool` | if include `__typename` field when querying sub types |


??? example
    ```py
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
    http request function must be set to make this function work, [click here to view](../http).


## ql.raw_query_response
takes raw query string and returns the response for
the given query
```py
def raw_query_response(query_str: str) -> QueryResponseDict
```

| Name | Type | Description |
|------|------|-------------|
| query_str | `str` | the graphql query string

??? example
    ```py
    response = ql.raw_query_response("""{
      point {
        x
        y
      }
    }""")
    ```


## ql.raw_query_response_scalar
takes raw query string, perfom an http request, and scalarize 
the response based on the '__typename'

```py
def raw_query_response_scalar(query_str) -> dict[str, QLModel | list[QLModel]]
```

!!! warning ""
    this functionality can only work if the query string
    contains the `__typename` field

| Name | Type | Description |
|------|------|-------------|
| query_str | `str` | the graphql query string |

??? example
    ```py
    response = ql.raw_query_response("""{
      point {
        x
        y
        __typename
      }
    }""")
    ```


## ql.query_response_scalar
serializes the ql query structure to a valid graphql query, send it via http, takes the response
and returns a scalared dict with the defined models, this function will also raise
graphql errors if the query responsed with `errors` field
```py
def query_response_scalar(
    *query_models: _QueryModelType, fragments: Optional[_QueryFragmentType] = None
) -> dict[str, BaseModel | list[BaseModel]]:
```

## ql.scalar_query_response
takes a graphql response `dict` and scalarize it based on the 
`__typename` field

```py
def scalar_query_response(
    query_reponse: QueryResponseDict,
) -> dict[str, QLModel | list[QLModel]]
```

!!! warning ""
    this functionality can only work if the query string
    contains the `__typename` field

| Name | Type | Description |
|------|------|-------------|
| query_response | `dict` | graphql query response |

??? example
    ```py
    import ql
    from pydantic import BaseModel

    @ql.model
    class Point(BaseModel):
      x: int
      y: int

    scalarized = ql.scalar_query_response({
      "point": {
        "x": 50,
        "y": 50,
        "__typename": "Point"
      }
    })
    assert isinstance(scalarized["point"], Point)
    ```

## ql.QueryBuilder
builder pattern to build graphql queries easily, allows all the functionality of [query_response](#qlquery_response), [scalar_query_response](#qlscalar_query_response) and [query](#qlquery)
in a nicer interface

| Name | Type | Description |
|------|------|-------------|
| include_typename | `bool` | if you include the `__typename` field |

??? example
    ```py
    import ql
    from pydantic import BaseModel

    @ql.model
    class Parent(BaseMode):
      first_name: str
      last_name: str

    @ql.model
    class Family(BaseModel):
      father: Parent
      mother: Parent

    scalared = (
      ql.QueryBuilder()
        .model(
          ql.QueryModelBuilder(Family)
            .model_field(
              ql.QueryModelBuilder("father")
                .fields(ql.fragment_ref("parent_query"))
            )
            .model_field(
              ql.QueryModelBuilder("mother")
                .fields(ql.fragment_ref("parent_query"))
            )
        )
        .fragment(
          ql.QueryFragmentBuilder("parent_query", Parent)
            .fields("first_name", "last_name")
        )
        .scalar()
    )
    ```

### .model()
takes a `QueryModelBuilder` to add new model query

```py
def model(self, model_builder: QueryModelBuilder) -> Self
```

| Name | Type | Description |
|------|------|-------------|
| model_builder | `QueryModelBuilder` | the query model builder instance |

### .fragment()
add fragment to the query

```py
def fragment(self, fragment_builder: QueryFragmentBuilder) -> Self
```

| Name | Type | Description |
|------|------|-------------|
| fragment_builder | `QueryFragmentBuilder` | the query fragment builder instance |

### .build()
returns the query as graphql string

```py
def build(self) -> str
```

### .query()
converts the query to string, performs http request and returns
the graphql response

```py
def query(self) -> QueryResponseDict
```

### .scalar()
converts the query to string, performs http request, and scalar the 
graphql request to python classes

```py
def scalar(self) -> dict[str, QLModel | list[QLModel]]
```

## ql.QueryModelBuilder
class that passed to `QueryBuilder` to build query for 
a specific model

| Name | Type | Description |
|------|------|-------------|
| model | `str | enum.Enum | type[QLModel]` | the model to build the query for |

### .fields()
add fields to query from the model

```py
def fields(self, *fields: QueryFieldTypes) -> Self
```

| Name | Type | Description |
|------|------|-------------|
| *fields | `QueryFieldTypes` | list of fields to add |

## ql.QueryFragmentBuilder
class to build fragments 

| Name | Type | Description |
|------|------|-------------|
| name | `str` | the fragment name |
| model | `str | enum.Enum | type[QLModel]` | the model to build the query for |

### .fields()
add fields to query from the model

```py
def fields(self, *fields: QueryFieldTypes) -> Self
```

| Name | Type | Description |
|------|------|-------------|
| *fields | `QueryFieldTypes` | list of fields to add |

### model_field
add field which is a sub model

```py
def model_field(self, model_builder: QueryModelBuilder) -> Self
```
