"""Module to define the exceptions for the Esign API."""
from vericlient.exceptions import VeriClientError


class EsignError(VeriClientError):
    """Base class for exceptions in the Esign API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidDocumentError(EsignError):
    """Exception raised when a document is invalid."""

    def __init__(self) -> None:
        message = "The document is invalid or malformed"
        super().__init__(message)


class DocumentNotFoundError(EsignError):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str) -> None:
        message = f"Document with ID {document_id} not found"
        super().__init__(message)


class SignatureRequestNotFoundError(EsignError):
    """Exception raised when a signature request is not found."""

    def __init__(self, request_id: str) -> None:
        message = f"Signature request with ID {request_id} not found"
        super().__init__(message)


class SignatureNotFoundError(EsignError):
    """Exception raised when a signature is not found."""

    def __init__(self, signature_id: str) -> None:
        message = f"Signature with ID {signature_id} not found"
        super().__init__(message)


class InvalidSignatureError(EsignError):
    """Exception raised when a signature is invalid."""

    def __init__(self) -> None:
        message = "The signature is invalid or malformed"
        super().__init__(message)
