---
title: "Welcome"
---
# Home
welcome to `ql`! a simple, light, fast and easy way to implement graphql client
in python with the help of [`pydantic`](https://docs.pydantic.dev/latest/).

the library is not intrusive, which means you won't find unexpected attributes
and functions attached to you pydantic model, and doesn't change the model behaviour.

!!! note
    the library does attach methods and properties to your model, but they always in the format of
    `__ql_<..>__`, so it is not expected you will ever call them accidentally.


```py title="simple like it should be"
import ql
from pydantic import BaseModel

@ql.model
class Person(BaseModel):
  first_name: str
  last_name: str
  age: int

response = ql.raw_query_response_scalar("""
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

---

# install
just `pip` install the package and start using it
```console
pip3 install pydantic-graphql
```
