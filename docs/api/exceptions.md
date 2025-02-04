# exceptions
exceptions are only raised in `scalar` requests, when we convert graphql
response to python objects it make sense to convert graphql errors to python exceptions.

graphql errors are always the same, if it returned an error you have a problem
with your query.

---

## ql.QLErrorResponseException
an exception class that is raised when scalar function
gets error response from graphql
```py
class QLErrorResponseException(Exception):
    def __init__(
        self,
        errors: list[QueryErrorDict]
    ) -> None:
```

| Name | Type | Description |
|------|------|-------------|
| `errors` | `list[QueryErrorDict]` | list of graphql errors |

??? example
    ```py
    import ql

    try:
      _ = ql.scalar_query_response({
        "errors": [
          {"message": "example for error", "locations": {"line": 0, "column": 0}},
          {"message": "I have another error in my query!", "locations": {"line": 0, "column": 0}},
        ],
        "data": None
      })
    except ql.QLErrorResponseException:
      print("damn... my graphql query failed...")
    ```

### `@property` error_details
returns a list of `QLErrorDetails`.

---

## ql.QLErrorDetails
class used to map each error detail to python object
```py
class QLErrorDetails:
    def __init__(
        self,
        message: str,
        locations: list[QueryErrorLocationDict]
    ) -> None:
```

| Name | Type | Description |
|------|------|-------------|
| `message` | `str` | the message field from the graphql error
| `locations` | `list[QueryErrorLocationDict]` | list of locations where the error occurse
