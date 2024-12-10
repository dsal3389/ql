__all__ = [
    "model",
    "all_models",
    "model_queryable_fields",
    "model_mutable_fields",
    "implements",
    "typename",
    "QueryBuilder",
    "QueryModelBuilder",
    "QueryFragmentBuilder",
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
    model_queryable_fields,
    model_mutable_fields,
    typename,
)
from ._query import (
    QueryBuilder,
    QueryModelBuilder,
    QueryFragmentBuilder,
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


@wraps(model_queryable_fields)
def _(*args, **kwargs):
    """thin wrapper around the `query_fields_nt`"""
    return model_queryable_fields(*args, **kwargs)
