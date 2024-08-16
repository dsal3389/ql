# model
modeling your graphql types is done with `pydantic`, and making the model
compatible with the `ql` library, use `lq.model`

## what `ql.model` does exactly?
this decorator defines couple of attributes that are required
for graphql apis and are used across the library.

| Name | Type | Description |
|------|------|-------------|
| `__ql_query_name__` | `str` | the model query name in graphql |
| `__ql_typename__` | `str` | the model `__typename` as it is in the graphql api, this will help us scalar responses |
| `__ql_implements__` | `dict[str, type[BaseModel]]` | inheriting models will register themselves the parents `__ql_implements__` |
| `__ql_query_fields_nt__` | `NamedTuple` | returns a named tuple with all queryable fields, the name tuple maps between the field to the graphql field name based on the `ql.metadata` attached to the field |




