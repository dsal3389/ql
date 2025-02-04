# query
querying is the most common operation, `ql` provides couple of ways to query
your data.

## raw query
raw querying just accepts your query string, as is, query functions
that accept raw query, are usally prefixed with `raw_`

!!! example
    ```py
    import ql

    response = ql.raw_query_response("""
    query {
        people {
            name
            age
        }
    }
    """)
    ```

## query python schema
`ql` also can takes a tuple of 2 values, value at index `0` is the model type, 
value at index `1` is iterable of fields.

!!! quote ""
    ```
    (<model>, (
        field, 
        field, 
        field, 
        ...
    ))
    ```

in code the query schema will look something like this

!!! example "python query schema in code"
    ```py
    import ql
    from pydantic import BaseModel


    @ql.model
    class Person(BaseModel):
        name: str
        age: int


    query_str = ql.query(
        (Person, (
            ql._(Person).name,
            ql._(Person).age
        ))
    )
    ```

!!! info "the `ql._` function"
    we wrap the model `Person` inside `ql._` to get the correct field queryname, more information
    about this function [click here](../api/model.md#qlquery_fields_nt)


### multiple models
since each tuple represent a "model" query in python,
`query` functions can take multuple "models", for example:

!!! quote ""
    ```py
    query_str = ql.query(
        (ModelA, (
            ql._(ModelA).foo,
            ...
        )),
        (ModelB, (
            ql._(ModelB).foo,
            ...
        )),
        ...
    )
    ```

### nested fields
lets first look at an example of querying nested fields

!!! example
    ```py
    query_str = ql.query(
        (Person, (
            ql._(Person).name,
            ql._(Person).age,
            (ql._(Person).child, (
                ql._(Child).name,
                ql._(Child).sleeps
            ))
        ))
    )
    ```

??? abstract "view full example"
    ```py
    import ql
    from pydantic import BaseModel


    @ql.model
    class Child(BaseModel):
        name: str
        sleeps: bool


    @ql.model
    class Person(BaseModel):
        name: str
        age: int
        child: Child


    query_str = ql.query(
        (Person, (
            ql._(Person).name,
            ql._(Person).age,
            (ql._(Person).child, (
                ql._(Child).name,
                ql._(Child).sleeps
            )),
        ))
    )
    ```

looks a bit more complicated. the nested schema is the same schema as before, but in the nested tuple at index `0`
we don't provide the model, we provide the `ql._(Person).child` field instead.

we can keep nesting like that as much as we want.

!!! quote ""
    ```
    (<model>, (
        field,
        field, 
        field,
        (field, (
            field,
            field,
            (field, (
                field,
                field,
                ...
            ))
        ))
    ))
    ```

## query builder pattern
building query with python objects is hard to read, raw queries are not type checkable,
a perfect pattern that solves both issues of readability and type checking is the builder pattern.

!!! example
    ```py
    import ql

    # models ...

    query_str = ql.QueryBuilder() \
        .model(
            ql.QueryModelBuilder(Person)
                .fields(
                    ql._(Person).first_name,
                    ql._(Person).last_name,
                    "age"  # string types are also allowed
                )
        ).build()

    # '{Person{first_name,last_name,age,__typename}}'
    ```

??? abstract "view full example"
    ```py
    import ql
    from pydantic import BaseModel

    @ql.model
    class Person(BaseModel):
        first_name: str
        last_name: str
        age: int

    query_str = ql.QueryBuilder() \
        .model(
            ql.QueryModelBuilder(Person)
                .fields(
                    ql._(Person).first_name,
                    ql._(Person).last_name,
                    "age"  # string types are also allowed
                )
        ).build()
        
    # '{Person{first_name,last_name,age,__typename}}'
    ```

### multiple models
the `QueryBuilder` has the `.model` method that accepts `QueryModelBuilder`, each
call to the `.model` method attaches the model to the query

!!! example
    ```py
    import ql
    from pydantic import BaseModel


    ```

??? abstract "view full example"

    ```py
    import ql
    from pydantic import BaseModel


    ```
