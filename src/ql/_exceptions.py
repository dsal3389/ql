from ._typing import QueryErrorDict, QueryErrorLocationDict


class QLErrorDetails:
    def __init__(self, message: str, locations: list[QueryErrorLocationDict]) -> None:
        self.message = message
        self.locations = locations

    def __str__(self) -> str:
        return self.message


class QLErrorResponseException(Exception):
    def __init__(self, errors: list[QueryErrorDict]) -> None:
        self.error_details = []

        for error in errors:
            self.error_details.append(
                QLErrorDetails(message=error["message"], locations=error["locations"])
            )

    def __str__(self) -> str:
        return "\n".join(map(str, self.error_details))
