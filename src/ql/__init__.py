__all__ = [
    "model",
    "all_models",
    "query_fields_nt",
    "mutate_fields_nt",
    "implements",
    "typename",
    "query",
    "query_response",
    "query_response_scalar",
    "scalar_query_response",
    "raw_query_response",
    "raw_query_response_scalar",
    "fragment_ref",
    "arguments",
    "on",
    "http",
    "metadata",
    "QueryResponseDict",
    "QLErrorResponseException",
    "QLErrorDetails",
    "_",
]

from ._http import http
from ._model import (
    model,
    all_models,
    implements,
    query_fields_nt,
    mutate_fields_nt,
    typename,
)
from ._query import (
    query,
    query_response,
    query_response_scalar,
    scalar_query_response,
    raw_query_response,
    raw_query_response_scalar,
    arguments,
    on,
    fragment_ref,
)
from ._typing import metadata, QueryResponseDict
from ._exceptions import QLErrorResponseException, QLErrorDetails

from functools import wraps


@wraps(query_fields_nt)
def _(*args, **kwargs):
    """thin wrapper around the `query_fields_nt`"""
    return query_fields_nt(*args, **kwargs)
