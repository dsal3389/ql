---
hide: toc
---
# about the library
this library is wrapped around pydantic for easy modeling, typechecking and 
because it is pydantic, it is well known package, no need to reinvent the wheel here.

## this library **is not**
  * an **http** client library, this library does not implement http communication with graphql endpoints.
  * a graphql server, this library is to create graphql client code.

## this library **is**
  * a light, fast and easy library to work with graphql apis.

# why use `ql` over other libraries

> At the time of writing this library does **NOT** support `mutation`, only `query`.

this library was written because when I searched for graphql client libraries, I couldn't
find easy/well written libraries for graphql, most of the libraries are small wrappers around `requests`,
or they are trying to reinvent the wheel, and they just feel awkward...

* `simplicity` - it is simple to query data, you can provide a query string, or generate a 
query string with python objects.

* `pydantic` - working with a well known library doesn't requires you to learn a lot of new things, also typechecking

* `scalar` - unlike other libraries, where there is no scalarize ability, or sometimes they require you to 
create a `Schema`, `ql` library takes use of the `__typename` field from graphql for scalarize functionality, which means,
you don't need to create `Schema` classes, and it can scalar from any given graphql response as long it includes the `__typename`
field for sub types


