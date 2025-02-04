# ql
Graphql client library, wrapped around pydantic classes for type validation,
provide simple, safe and pythonic way to query data from a graphql api.

using pydantic for creating python objects from rest api is common, it is easy and 
it has type validation, so why not make it easy also for graphql apis?

features:
  * python objects to valid graphql string
  * http send and recv information
  * scalar query responses

## install
```console
pip3 install pydantic-graphql
```

## documentation 
[https://dsal3389.github.io/ql/](https://dsal3389.github.io/ql/)

# local development

## install
install locally
```sh
git clone git@github.com:dsal3389/ql.git
```

## documentation
make sure you are at the project root
```sh
poetry run mkdocs serve
```

## tests
library uses pytest to validate that behavior is expected
```sh
poetry run pytest
```

