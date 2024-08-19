from typing import Callable, TypeAlias, Optional
from ._typing import QueryResponseDict


GraphqlRequestFunc: TypeAlias = Callable[[dict[str, str]], QueryResponseDict]


class _QLHTTPClient:
    """
    ql library main http client, it doesn't preform the request by itself,
    but expect to get an outside function that does that request for it, this is
    the case because graphql authentication methods and connection
    handling can vary
    """

    __slots__ = ("_request_func",)

    def __init__(self) -> None:
        self._request_func: Optional[GraphqlRequestFunc] = None

    def set_request_func(self, request_func: GraphqlRequestFunc) -> None:
        """set the library graphql request function, if already set, overwrite"""
        if not callable(request_func):
            raise ValueError(
                "`ql.http.set_request_query_func` expectes to get a callable function"
            )
        self._request_func = request_func

    def request_query(self, query: str) -> QueryResponseDict:
        """preform request with the provided request function, if no request function is set, raise `ValueError`"""
        return self._request({"query": query})

    def request_mutate(self, mutation: str) -> QueryResponseDict:
        return self._request({"mutate": mutation})

    def _request(self, data: dict[str, str]) -> QueryResponseDict:
        if self._request_func is None:
            raise ValueError(
                "ql cannot preform http request, set a request function `ql.http.set_request_func`"
            )
        return self._request_func(data)


http = _QLHTTPClient()
