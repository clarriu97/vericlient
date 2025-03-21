"""Module to define the exceptions for the Validas API."""
from typing import List, Dict, Optional
from vericlient.exceptions import VeriClientError


class ValidasError(VeriClientError):
    """Base class for exceptions in the Validas API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


# Validation Process Errors
class ValidationProcessError(ValidasError):
    """Base class for validation process errors."""


class IncompleteValidationError(ValidationProcessError):
    """Raised when the validation process is incomplete."""

    def __init__(self) -> None:
        super().__init__("The validation process is incomplete")


class NotAllowedError(ValidationProcessError):
    """Raised when an operation is not allowed on the validation."""

    def __init__(self, message: str = "The requested operation is not allowed") -> None:
        super().__init__(message)


class ValidationFormError(ValidationProcessError):
    """Raised when the provided information in a form is not valid."""

    def __init__(self, form_errors: Optional[Dict[str, List[str]]] = None) -> None:
        super().__init__("Invalid form data")
        self.errors = []
        if form_errors:
            for field, errors in form_errors.items():
                for error in errors:
                    self.errors.append({"field": field, "error": error})


# Document Related Errors
class DocumentError(ValidasError):
    """Base class for document-related errors."""


class DocumentServiceError(DocumentError):
    """Base class for document service errors."""

    def __init__(self, message: str, analysis_type: Optional[str] = None, 
                 http_status: int = 400, errors: Optional[List[Dict]] = None) -> None:
        if analysis_type:
            message = f"{analysis_type} Document Analysis error: {message}"
        super().__init__(message)
        self.http_status = http_status
        self.errors = errors


class EmptyDocumentError(DocumentError):
    """Raised when a document file is empty."""

    def __init__(self, analysis_type: Optional[str] = None) -> None:
        message = "Document file is empty"
        if analysis_type:
            message = f"{analysis_type} document file is empty"
        super().__init__(message)
        self.analysis_type = analysis_type


class InvalidDocumentError(DocumentError):
    """Raised when a document is invalid."""

    def __init__(self, analysis_type: Optional[str] = None) -> None:
        message = "Invalid document"
        if analysis_type:
            message = f"Invalid {analysis_type} document"
        super().__init__(message)
        self.analysis_type = analysis_type


class DocumentServiceNotAvailableError(DocumentError):
    """Raised when the document service is not available."""

    def __init__(self) -> None:
        super().__init__("Document service is not available")


class DocumentValidationError(DocumentError):
    
    """Raised when there's an error in the document validation process."""
    def __init__(self, message: str, analysis_type: str = None):
        self.analysis_type = analysis_type
        super().__init__(message)


# Selfie and Video Related Errors
class BiometricError(ValidasError):
    """Base class for biometric-related errors."""


class EmptySelfieError(BiometricError):
    """Raised when a selfie file is empty."""

    def __init__(self) -> None:
        super().__init__("Selfie file is empty")


class EmptyVideoError(BiometricError):
    """Raised when a video file is empty."""

    def __init__(self) -> None:
        super().__init__("Video file is empty")


class EmptyAnnotationsError(BiometricError):
    """Raised when an annotations file is empty."""

    def __init__(self) -> None:
        super().__init__("Annotations file is empty")


class InvalidVideoError(BiometricError):
    """Raised when a video is invalid."""

    def __init__(self, message: str = "Invalid video format") -> None:
        super().__init__(message)


class VideoPhotoChallengeError(BiometricError):
    """Raised when there's an error with video-photo challenge."""

    def __init__(self) -> None:
        super().__init__("Video-photo challenge not allowed: selfie already analyzed")


# Challenge Related Errors
class ChallengeError(ValidasError):
    """Base class for challenge-related errors."""


class UnknownChallengeTypeError(ChallengeError):
    """Raised when the challenge type is unknown."""

    def __init__(self) -> None:
        super().__init__("Unknown challenge type")


class InvalidTokenError(ChallengeError):
    """Raised when the challenge token is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid challenge token")


# Service Mode Errors
class ServiceModeError(ValidasError):
    """Base class for service mode errors."""


class NotAllowedServiceModeError(ServiceModeError):
    """Raised when the service mode is not allowed."""

    def __init__(self) -> None:
        super().__init__("Service mode not allowed")


# Resource Not Found Errors
class ResourceNotFoundError(ValidasError):
    """Base class for resource not found errors."""


class ImageNotFoundError(ResourceNotFoundError):
    """Raised when an image is not found."""

    def __init__(self) -> None:
        super().__init__("Image not found")


class VideoNotFoundError(ResourceNotFoundError):
    """Raised when a video is not found."""

    def __init__(self) -> None:
        super().__init__("Video not found")


class FileNotFoundError(ResourceNotFoundError):
    """Raised when a file is not found."""

    def __init__(self) -> None:
        super().__init__("File not found")


# Configuration Errors
class ConfigurationError(ValidasError):
    """Base class for configuration errors."""


class InvalidScoresConfigurationError(ConfigurationError):
    """Raised when the scores configuration is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid scores configuration")


class ScoresConfigurationNotAllowedError(ConfigurationError):
    """Raised when scores configuration is not allowed."""

    def __init__(self) -> None:
        super().__init__("Scores configuration only allowed in obverse analysis")


# Identity Verification Errors
class IdentityVerificationError(ValidasError):
    """Base class for identity verification errors."""


class IdentityVerificationServiceError(IdentityVerificationError):
    """Raised when there's an error with the identity verification service."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Identity verification error: {message}")


class UnavailableIdentityVerificationError(IdentityVerificationError):
    """Raised when identity verification service is not available."""

    def __init__(self) -> None:
        super().__init__("Identity verification service not available")


# Processing Errors
class ProcessingError(ValidasError):
    """Base class for processing errors."""


class ErrorProcessingRequestError(ProcessingError):
    """Raised when there's an error processing a request."""

    def __init__(self) -> None:
        super().__init__("Error processing request: another request is being processed")
