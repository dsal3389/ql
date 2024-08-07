__all__ = [
    "model",
    "all_models",
    "query_fields_nt",
    "mutate_fields_nt",
    "implements",
    "query",
    "query_response",
    "arguments",
    "on",
    "http",
    "metadata",
    "_",
]

from .http import http
from .model import (
    model,
    all_models,
    implements,
    query_fields_nt,
    mutate_fields_nt,
)
from .query import query, query_response, arguments, on
from .typing import metadata

from functools import wraps


@wraps(query_fields_nt)
def _(*args, **kwargs):
    """thin wrapper around the `query_fields_nt`"""
    return query_fields_nt(*args, **kwargs)
