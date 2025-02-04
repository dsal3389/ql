# Query examples

---

## raw query
raw query is when we use place the graphql query in python string

!!! quote
    ```py
    graphql_response = ql.raw_query_response("""
      query {
        Person {
          name
          age
        }
      }
    """)
    ```

??? abstract "full example view"
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

### scalar

!!! quote
    ```py
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

??? abstract "full example view"
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

---

## builder pattern
the builder pattern allows for type checking, readability and the use of python
object to create dynamic queries

### scalar

!!! quote
    ```py
    query = ql.QueryBuilder()
      .model(
        ql.QueryModelBuilder(Human)
          .fields(
            ql._(Human).name,
            ql._(Human).age
          )
      )
      .scalar()  # also possible options `build` and `query`
    ```

??? abstract "view full example"
    ```py
    import ql
    from pydantic import BaseModel

    @ql.model
    class Human(BaseModel):
      name: str
      age: int


    query = ql.QueryBuilder()
      .model(
        ql.QueryModelBuilder(Human)
          .fields(
            ql._(Human).name,
            ql._(Human).age
          )
      )
      .scalar()  # also possible options `build` and `query`
    ```

---

## python tuples

!!! quote
    ```py
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


??? abstract "view full example"
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
