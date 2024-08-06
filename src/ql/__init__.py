__all__ = [
    "model",
    "query_fields_nt",
    "mutate_fields_nt",
    "implements",
    "query",
    "arguments",
    "metadata",
    "_",
]

from .model import (
    model,
    implements,
    query_fields_nt,
    mutate_fields_nt,
)
from .query import query, arguments
from .typing import metadata

from functools import wraps


@wraps(query_fields_nt)
def _(*args, **kwargs):
    """thin wrapper around the `query_fields_nt`"""
    return query_fields_nt(*args, **kwargs)
