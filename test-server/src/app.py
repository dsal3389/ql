import strawberry
from tinydb import TinyDB, Query
from typing import Optional


db = TinyDB("./database.json")


@strawberry.type
class User:
    name: str
    email: str
    age: int

    class db:
        query: Query = Query()
        table = db.table("table_user")


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: str) -> Optional[User]:
        user_data = User.db.table.get(User.db.query.name == name)

        if user_data:
            return User(**user_data)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_user(self, name: str, email: str, age: int) -> User:
        user_data = {"name": name, "email": email, "age": age}
        User.db.table.insert(user_data)
        return User(**user_data)


schema = strawberry.Schema(query=Query, mutation=Mutation)
