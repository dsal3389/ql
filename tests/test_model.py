import ql
from tests.models import Human, Male, Female, Child


def test_implments() -> None:
    implemented_models = (Male, Female, Child)

    for implemented_model in implemented_models:
        assert (
            implemented_model in ql.implements(Human)
        ), f"model `Human` implements `{implemented_model.__name__}` but couldn't find it in the implements list of `Human`"
