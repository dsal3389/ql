# ql
graphql library for python to create graphql queries with python pydantic objects

> ```py
> import ql
> from pydantic import BaseModel
> 
> 
> @ql.model
> class Point(BaseModel):
>   x: int
>   y: int
> 
> 
> q = ql.query(
>   (Point, (
>     q._(Point).x,
>     q._(Point).y
>   ))
> )
> print(q)
> ```
> ---
> ```
> query{Point{x,y}}
> ```

## different query names then what defined
> ```py
> import ql
> from pydantic import BaseModel, Field
> 
> 
> @ql.model(query_name="Person")
> class Adult(BaseModel):
>   name: Annotation[str, ql.metadata(query_name="first_name")]
>
> q = ql.query((Adult,(ql._(Adult).name,))
> print(q)
> ```
> ---
> ```
> query{Person{first_name}}
> ```

## smart implements
> ```py
> import ql
> from pydantic import BaseModel
>
> @ql.model
> class Human(BaseModel):
>   first_name: str
>   last_name: str
>
> @ql.model
> class Female(Human):
>   pass
>
> @ql.model
> class Male(Human):
>   passs
>
> print(ql.implements(Human))  # what does `Human` implement
> ```
> ---
> ```
> frozenset({<class '__main__.Human'>})
> ```
