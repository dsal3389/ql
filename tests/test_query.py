import ql
import pytest
from tests.models import Point, Family, Human, Male, Female


def test_stringify_query() -> None:
    assert (
        ql.query((Point, (ql._(Point).x, ql._(Point).y)), include_typename=False)
        == "query{Point{x,y}}"
    ), "simple querying without including typename failed"
    assert (
        ql.query((Point, (ql._(Point).x, ql._(Point).y)))
        == "query{Point{x,y,__typename}}"
    ), "simple querying with including typename failed"


def test_nested_query() -> None:
    assert (
        ql.query(
            (
                Family,
                (
                    ql._(Family).count,
                    (
                        ql._(Family).people,
                        (
                            ql._(Human).first_name,
                            (ql.on(Male), (ql._(Male).sick,)),
                            (ql.on(Female), (ql._(Female).pregnant,)),
                        ),
                    ),
                ),
            )
        )
        == "query{family{count,people{first_name,...on Male{sick,__typename},...on Female{pregnant,__typename},__typename},__typename}}"
    )


def test_invalid_query() -> None:
    with pytest.raises(ValueError):
        ql.query(
            (
                Point,
                (
                    ql._(Point).x,
                    (ql._(Point).y,),  # tuple in the middle of the fields list
                ),
            )
        )

    with pytest.raises(ValueError):
        ql.query(
            (
                Human,
                (
                    ql._(Human).first_name,
                    ql.on(Female),  # random inline fragment
                ),
            )
        )


def test_scalar_query_response() -> None:
    scalared = ql.scalar_query_response(
        {
            "data": {
                "family": [
                    {
                        "count": 55,
                        "people": [
                            {
                                "first_name": "foo",
                                "last_name": "oof",
                                "alive": True,
                                "sick": False,
                                "__typename": "Male",
                            }
                        ],
                        "__typename": "Family",
                    },
                ]
            }
        }
    )
    assert scalared == {
        "family": [
            Family(
                count=55,
                people=[
                    Male(
                        first_name="foo",
                        last_name="oof",
                        alive=True,
                        sick=False,
                    )
                ],
            )
        ]
    }
