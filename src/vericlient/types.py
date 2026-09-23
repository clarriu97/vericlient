"""Field types shared by the input models.

These exist for the error messages. A plain `str | bytes` annotation makes pydantic report
one failure per branch of the union — *"should be a valid string"* and *"should be a valid
bytes"* — neither of which is the thing the caller got wrong, and both at once. A validator
in front of the union reports it once, in the terms the library actually uses.
"""

from typing import Annotated

from pydantic import BeforeValidator

MEDIA_ERROR = "expected a path to a file, or its content as bytes"


def _media(value: object) -> object:
    # A TypeError would read better on its own, but pydantic turns either into the same
    # ValidationError, and ValueError is the one it documents for a validator.
    if not isinstance(value, (str, bytes)):
        raise ValueError(MEDIA_ERROR)  # noqa: TRY004
    return value


Media = Annotated[str | bytes, BeforeValidator(_media)]
"""A file the caller supplies: a path to it, or its content as bytes."""
