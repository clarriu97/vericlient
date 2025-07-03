"""Module to define the exceptions for the VCSP API."""
from vericlient.exceptions import VeriClientError


class VcspError(VeriClientError):
    """Base class for exceptions in the VCSP API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class EmptyFileError(VcspError):
    """Exception raised for empty files."""

    def __init__(self) -> None:
        message = "The file provided is empty"
        super().__init__(message)


class RequestValidationError(VcspError):
    """Exception raised for request validation error."""

    def __init__(self) -> None:
        message = "The request is invalid"
        super().__init__(message)


class UnsupportedMediaTypeError(VcspError):
    """Exception raised for unsupported media type."""

    def __init__(self) -> None:
        message = "The media type is not supported"
        super().__init__(message)


class InvalidClaimsError(VcspError):
    """Exception raised for invalid claims."""

    def __init__(self) -> None:
        message = "The claims provided don't match the required schema"
        super().__init__(message)


class InvalidAssuranceError(VcspError):
    """Exception raised for invalid assurance."""

    def __init__(self) -> None:
        message = "The assurance provided doesn't match the required schema"
        super().__init__(message)


class InvalidTagsError(VcspError):
    """Exception raised for invalid tags."""

    def __init__(self) -> None:
        message = "Specified tags don't exist"
        super().__init__(message)


class InvalidCredentialConfigurationUrnError(VcspError):
    """Exception raised for invalid credential configuration urn."""

    def __init__(self) -> None:
        message = "Specified credential configuration URN doesn't exist"
        super().__init__(message)


class InvalidAssuranceMethodUrnError(VcspError):
    """Exception raised for invalid assurance method."""

    def __init__(self) -> None:
        message = "Specified assurance method URN doesn't exist"
        super().__init__(message)


class CredentialConfigurationUrnAlreadyAssignedError(VcspError):
    """Exception raised for already assigned credential configuration urn."""

    def __init__(self) -> None:
        message = "The specified credential configuration URN is already assigned to the applicant"
        super().__init__(message)


class InvalidAudioFormatError(VcspError):
    """Exception raised for invalid audio format."""

    def __init__(self) -> None:
        message = "The audio format is not supported"
        super().__init__(message)


class InvalidSnrError(VcspError):
    """Exception raised for invalid signal noise ratio."""

    def __init__(self) -> None:
        message = "Invalid signal noise ratio"
        super().__init__(message)


class VoiceDurationIsNotEnoughError(VcspError):
    """Exception raised for voice duration not enough."""

    def __init__(self) -> None:
        message = "Voice duration is not enough"
        super().__init__(message)


class InsufficientQualityError(VcspError):
    """Exception raised for insufficient quality."""

    def __init__(self) -> None:
        message = "The audio quality is insufficient or may contain more than one speaker"
        super().__init__(message)


class FaceNotFoundError(VcspError):
    """Exception raised for face not found."""

    def __init__(self) -> None:
        message = "Face not found"
        super().__init__(message)


class MoreThanOneFaceError(VcspError):
    """Exception raised for more than one face."""

    def __init__(self) -> None:
        message = "More than one face found"
        super().__init__(message)


class FaceTooSmallError(VcspError):
    """Exception raised for face too small."""

    def __init__(self) -> None:
        message = "Face too small"
        super().__init__(message)


class FaceAlignmentError(VcspError):
    """Exception raised for face alignment error."""

    def __init__(self) -> None:
        message = "Face alignment error"
        super().__init__(message)


class AssuranceMethodNotFoundError(VcspError):
    """Exception raised for assurance method not found."""

    def __init__(self) -> None:
        message = "Assurance method not found"
        super().__init__(message)


class AssuranceValidationError(VcspError):
    """Exception raised for assurance validation error."""

    def __init__(self) -> None:
        message = "Assurance validation error"
        super().__init__(message)


class AccountNotFoundError(VcspError):
    """Exception raised for account not found."""

    def __init__(self) -> None:
        message = "Account not found"
        super().__init__(message)


class CredentialNotFoundError(VcspError):
    """Exception raised for credential not found."""

    def __init__(self) -> None:
        message = "Credential not found"
        super().__init__(message)


class GroupNotFoundError(VcspError):
    """Exception raised for group not found."""

    def __init__(self) -> None:
        message = "Group not found"
        super().__init__(message)


class GroupsLimitExceededError(VcspError):
    """Exception raised for group limit exceeded."""

    def __init__(self) -> None:
        message = "Group limit exceeded"
        super().__init__(message)


class EnrollmentsLimitExceededError(VcspError):
    """Exception raised for enrollment limit exceeded."""

    def __init__(self) -> None:
        message = "Enrollment limit exceeded"
        super().__init__(message)


class GroupAlreadyExistsError(VcspError):
    """Exception raised for group already exists."""

    def __init__(self) -> None:
        message = "Group already exists"
        super().__init__(message)


class TagsLimitExceededError(VcspError):
    """Exception raised for tags limit exceeded."""

    def __init__(self) -> None:
        message = "Tags limit exceeded"
        super().__init__(message)
