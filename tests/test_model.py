import ql
from tests.models import Human, Male, Female


def test_implments() -> None:
    assert Male in ql.implements(
        Human
    ), "model `Human` implements model `Male`, but couldn't find it"
    assert Female in ql.implements(
        Human
    ), "model `Human` implements model `Female` but couldn't find it"
