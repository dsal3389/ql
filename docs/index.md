# Welcome
welcome to `ql`! a simple, light, fast and easy way to implement graphql client
in python with the help of [`pydantic`](https://docs.pydantic.dev/latest/).

the library is not intrusive, which means you won't find unexpected attributes
and functions attached to you pydantic model, and doesn't change the model behaviour.

!!! note
    the library does attach methods and properties to your model, but they always in the format of
    `__ql_<..>__`, so it is not expected you will ever call them accidentally.


<div class="annotate" markdown>
```py title="simple like it should be" 
import ql
from pydantic import BaseModel

@ql.model  # (1)
class Person(BaseModel):
  first_name: str
  last_name: str
  age: int

response = ql.raw_query_response_scalar("""  (2)
query {
  Person(first_name: "foo") {
    first_name
    last_name
    age
    __typename  # required for scalar
  }
}
""")
# {"person": Person(first_name="foo", last_name="oof", age=99)}
```
</div>

1. makes the pydantic model compatible to use with the library
2. function that takes a raw query string, send it via http, and scalarize the response base on the `__typename`

---

# install
just `pip` install the package and start using it
```console
pip3 install pydantic-graphql
```
