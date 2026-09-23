"""Module to define the exceptions for the das-Face API.

das-Face reports failures differently from the other services: its error bodies carry
`{code, message, status}`, where das-Peak uses `{error, exception}` and VCSP uses
`{error, title, reason}`.

The v3.35 specification enumerates these codes properly, which v3.26 did not. Three of the
codes below are not in it: `UnknownHashAndModeError` and `PathNotFoundError`, both found
against `work`/`eu`, and `ExpiredOrInvalidChallengeError`, which v3.26 documents for the
challenge endpoints that v3.35 dropped.
"""

from vericlient.exceptions import VeriClientError


class DasfaceError(VeriClientError):
    """Base class for exceptions in the das-Face API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FaceNotFoundError(DasfaceError):
    """Exception raised when no face could be located in the image."""

    def __init__(self) -> None:
        message = "No face was found in the image."
        super().__init__(message)


class MoreThanOneFaceError(DasfaceError):
    """Exception raised when the image holds more than one face."""

    def __init__(self) -> None:
        message = "More than one face was found in the image; it has to hold exactly one."
        super().__init__(message)


class FaceAlignmentError(DasfaceError):
    """Exception raised when the face's key points could not be located."""

    def __init__(self) -> None:
        message = "The face was found but its key points could not be located, so it cannot be analysed."
        super().__init__(message)


class ObsoleteCredentialModelError(DasfaceError):
    """Exception raised when a credential was generated with a model the service has dropped.

    Worth catching on its own: it means the credential has to be regenerated from the
    original photo, not that the request was wrong.
    """

    def __init__(self) -> None:
        message = (
            "The credential was generated with a model the service no longer offers. Generate a new one from the original photo."
        )
        super().__init__(message)


class IncompatibleCredentialsError(DasfaceError):
    """Exception raised when two credentials cannot be compared with each other.

    Credentials are only comparable when they come from the same model and mode.
    """

    def __init__(self) -> None:
        message = "The credentials were generated with different models, so they cannot be compared."
        super().__init__(message)


class ZeroLengthVideoError(DasfaceError):
    """Exception raised when the video is empty or was corrupted in transit."""

    def __init__(self) -> None:
        message = "The video is empty or was corrupted in transit."
        super().__init__(message)


class NotEnoughVideoDataError(DasfaceError):
    """Exception raised when the video holds too few usable frames to analyse."""

    def __init__(self) -> None:
        message = "The video does not hold enough usable frames to analyse."
        super().__init__(message)


class VideoExtractionError(DasfaceError):
    """Exception raised when the video could not be decoded."""

    def __init__(self) -> None:
        message = "The video could not be decoded. Check its container and codec."
        super().__init__(message)


class InvalidVideoMetadataError(DasfaceError):
    """Exception raised when the video's frame rate or frame count are not usable.

    das-Face reports these as two separate codes, `InvalidFPSVideoError` and
    `InvalidNumFramesVideoError`; both mean the same thing to a caller.
    """

    def __init__(self) -> None:
        message = "The video's frame rate or frame count is not valid."
        super().__init__(message)


class FaceTooSmallForIasError(DasfaceError):
    """Exception raised when the face is too small for the authenticity analysis."""

    def __init__(self) -> None:
        message = (
            "The face is too small for the authenticity analysis. Its bounding box has to be "
            "wider; a larger photo, or one where the face fills more of the frame, will pass."
        )
        super().__init__(message)


class FormValidationError(DasfaceError):
    """Exception raised when the request body is not what the endpoint expects.

    das-Face uses one code for every malformed input: an image that is not decodable, a
    string that is not valid base64, a credential that is not a credential, and a missing
    required field all arrive as this.

    The service splits the explanation in two. Its `message` names the form it was validating
    — `Incorrect parameters in GenerateSequentialChallengeForm` — and its `errors` name the
    field and what is wrong with it. Only the second half is any use, so both are reported
    and `errors` is kept for a caller that wants to act on a specific field.

    Attributes:
        errors: The `(field, reason)` pairs the service listed, empty if it listed none

    """

    def __init__(self, message: str | None = None, errors: list[tuple[str, str]] | None = None) -> None:
        self.errors = errors or []
        fields = "; ".join(f"{field}: {reason}" for field, reason in self.errors)
        detail = ": " + " — ".join(part for part in (message, fields) if part) if message or fields else "."
        super().__init__(f"The request was rejected as invalid{detail}")


class UnknownHashAndModeError(DasfaceError):
    """Exception raised when no biometrics model matches the given hash and mode."""

    def __init__(self) -> None:
        message = "No biometrics model matches that hash and mode. Use get_models() to list them."
        super().__init__(message)


class PathNotFoundError(DasfaceError):
    """Exception raised when the endpoint is not available on the target deployment.

    Some endpoints in the specification are not enabled everywhere. On the EU sandbox,
    `authenticity/photo/unequal-pair` answers with this.
    """

    def __init__(self) -> None:
        message = "The service does not expose that endpoint. It may not be enabled for this deployment."
        super().__init__(message)


class DasfaceApiError(DasfaceError):
    """Exception raised for a failure das-Face reports with a code this client does not map.

    The specification documents only status codes, so the set of codes is discovered by
    provoking them. Rather than swallow an unrecognised one into a generic server error, it
    is surfaced with the code and message the service gave, which is what an integrator needs
    to report it.
    """

    def __init__(self, code: str, message: str | None = None) -> None:
        detail = f": {message}" if message else ""
        super().__init__(f"The service reported {code}{detail}")
        self.code = code


class ExpiredOrInvalidChallengeError(DasfaceError):
    """Exception raised when a challenge token is no longer accepted.

    A challenge is valid for as long as its `expiration` said, 1800 seconds by default. Past
    that the recording cannot be analysed and a fresh challenge has to be generated.
    """

    def __init__(self) -> None:
        message = "The challenge has expired or is not valid. Generate a new one."
        super().__init__(message)
