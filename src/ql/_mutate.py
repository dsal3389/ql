from typing import Generator, Any, Optional, TypeAlias

# mutate request is a tuple of mutate name, mutate data, response query
MutateRequestSchema: TypeAlias = tuple[str, dict, Optional[str | tuple[str, ...]]]


class _MutateSerializer:
    __slots__ = ("_mutates",)

    def __init__(self, mutates: tuple[MutateRequestSchema, ...]) -> None:
        self._mutates = mutates

    def serialize(self) -> str:
        return "".join(self._serialize_mutate_dict())

    def _serialize_mutate_dict(self) -> Generator[str, None, None]:
        yield "mutation{"
        for mutate_name, mutate_data, return_query in self._mutates:
            yield mutate_name
            yield "("
            yield from self._serialize_dict(mutate_data)
            yield ")"

            if return_query is None:
                yield "{}"
            elif isinstance(return_query, (tuple, list, set)):
                yield "{"
                yield ",".join(return_query)
                yield "}"
            else:
                yield return_query
        yield "}"

    def _serialize_dict(self, dict_: dict) -> Generator[str, None, None]:
        first = True
        for key, value in dict_.items():
            if not first:
                yield ","
            first = False

            yield from self._serialize_dict_key(key)
            yield ":"
            yield from self._serialize_dict_value(value)

    def _serialize_dict_key(self, key: Any) -> Generator[str, None, None]:
        if isinstance(key, str):
            yield key
        else:
            raise ValueError(
                f"mutate dict key cannot be of value `{type(key).__name__}`"
            )

    def _serialize_dict_value(self, value: Any) -> Generator[str, None, None]:
        if isinstance(value, str):
            yield f'"{value}"'
        elif isinstance(value, int):
            yield str(value)
        elif isinstance(value, bool):
            yield str(value).lower()
        elif isinstance(value, dict):
            yield "{"
            yield from self._serialize_dict(value)
            yield "}"
        else:
            raise ValueError(
                f"couldn't serialize mutate dict value of type `{type(value).__name__}`"
            )


def mutate(*mutates: MutateRequestSchema) -> str:
    return _MutateSerializer(mutates).serialize()
