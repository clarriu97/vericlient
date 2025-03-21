"""Module to define the models for the Esign API."""
from typing import Any

from pydantic import BaseModel, field_validator


class EsignResponse(BaseModel):
    """Base class for the Esign API responses.

    Attributes:
        status_code: The status code of the response

    """

    status_code: int


class LibraryDocumentInput(BaseModel):
    """Input class for creating a library document.

    Attributes:
        name: Name of the document
        file: The file content (path or bytes)
        form_fields_per_document: Optional form fields for the document

    """

    name: str
    file: str | bytes
    form_fields_per_document: list[dict[str, Any]] | None = None

    @field_validator("file")
    def must_be_str_or_bytes(cls, value: object) -> str | bytes:
        """Validate that the file is a string or bytes object."""
        if not isinstance(value, (str, bytes)):
            error = "file must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class LibraryDocumentOutput(EsignResponse):
    """Output class for library document operations.

    Attributes:
        id: The ID of the document
        name: Name of the document

    """

    id: str
    name: str


class SecurityOptions(BaseModel):
    """Security options for signers.

    Attributes:
        auth_method: Authentication method (e.g., "password", "code")
        password: Optional password for authentication

    """

    auth_method: str
    password: str | None = None


class SignerInput(BaseModel):
    """Input class for a signer.

    Attributes:
        name: Name of the signer
        email: Email of the signer
        order: Order in which the signer should sign
        role: Role of the signer (e.g., "SIGNER", "VALIDATOR")
        security_options: Security options for signer authentication

    """

    name: str
    email: str
    order: int
    role: str
    security_options: SecurityOptions


class SignatureRequestInput(BaseModel):
    """Input class for creating a signature request.

    Attributes:
        title: Title of the signature request
        type: Type of the signature request
        signers: List of signers
        library_document_ids: List of document IDs
        ready: Whether the request is ready to be sent

    """

    title: str
    type: str = "manual"
    signers: list[SignerInput]
    library_document_ids: list[str]
    ready: bool = False


class SignatureRequestOutput(EsignResponse):
    """Output class for signature request operations.

    Attributes:
        id: The ID of the signature request
        title: Title of the signature request
        status: Status of the request

    """

    id: str
    title: str
    status: str


class SignatureInput(BaseModel):
    """Input class for signing a document.

    Attributes:
        name_or_initials: Name or initials for the signature
        selfie: Optional selfie image

    """

    name_or_initials: str
    selfie: str | bytes | None = None

    @field_validator("selfie")
    def must_be_str_or_bytes(cls, value: object) -> str | bytes:
        """Validate that the selfie is a string or bytes object."""
        if value is not None and not isinstance(value, (str, bytes)):
            error = "selfie must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class SignatureOutput(EsignResponse):
    """Output class for signature operations.

    Attributes:
        id: The ID of the signature
        status: Status of the signature
        status_code: Status code of the response

    """

    id: str
    status: str | None = None
    status_code: str | None = None
