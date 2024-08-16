# http
this library does not implement http communication with graphql server since API can be
different from implementation to implementation. the library http client accept a `request` function
that takes a graphql query string, and returns the json response parsed as dict, this allows 
the flexability to implement error handlers in the passed request function instead
of wrapping each `query` request with `try...except`.


##  ql.http.set_request_func
set request function for the `ql` client
```py
def set_request_func(request_func: GraphqlRequestFunc) -> None:
```

| Name | Type | Description |
|------|------|-------------|
| `request_func` | `GraphqlRequestFunc` | callable function that accepts a string and returns dict |

```py title="example.py"
import ql
import requests

def request_graphql(query: str) -> dict:
  response = requests.post("...", json={"query": query})
  response.raise_for_status()  # can handle errors here in one place
  return response.json()

ql.http.set_request_func(request_graphql)
```

---

## ql.http.request
send request query with given request function
```py
def request(self, query: str) -> QueryResponseDict:
```

| Name | Type | Description |
|------|------|-------------|
| `query` | `str` | the query request that will be passed to the function |


