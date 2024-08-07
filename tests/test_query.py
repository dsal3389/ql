import ql
from tests.models import Point


def test_stringify_query() -> None:
    assert (
        ql.query((Point, (ql._(Point).x, ql._(Point).y)), include_typename=False)
        == "query{Point{x,y}}"
    ), "simple querying without including typename failed"

    assert (
        ql.query((Point, (ql._(Point).x, ql._(Point).y)))
        == "query{Point{x,y,__typename}}"
    ), "simple querying with including typename failed"
