"""Implementation of the client for the Esign service."""
import json

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.esign.endpoints import EsignEndpoints
from vericlient.esign.exceptions import (
    DocumentNotFoundError,
    InvalidDocumentError,
    InvalidSignatureError,
    SignatureNotFoundError,
    SignatureRequestNotFoundError,
)
from vericlient.esign.models import (
    LibraryDocumentInput,
    LibraryDocumentOutput,
    SignatureInput,
    SignatureOutput,
    SignatureRequestInput,
    SignatureRequestOutput,
)
from vericlient.exceptions import VeriClientError
from vericlient.utils import get_virtual_file


class EsignClient(Client):
    """Class to interact with the Esign API."""

    def __init__(
            self,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the EsignClient class.

        Args:
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        api = APIs.ESIGN.value
        super().__init__(
            api=api,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        self._exceptions = [
            "InvalidDocumentException",
            "DocumentNotFoundException",
            "SignatureRequestNotFoundException",
            "SignatureNotFoundException",
            "InvalidSignatureException",
            "ServerError",
        ]
        self._exception_map = {
            "InvalidDocumentException": InvalidDocumentError,
            "DocumentNotFoundException": self._handle_document_not_found,
            "SignatureRequestNotFoundException": self._handle_signature_request_not_found,
            "SignatureNotFoundException": self._handle_signature_not_found,
            "InvalidSignatureException": InvalidSignatureError,
        }

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API."""
        response_json = response.json()

        exception = response_json.get("exception")
        if not exception or exception not in self._exceptions:
            self._raise_server_error(response)

        handler = self._exception_map.get(exception)
        if handler:
            if isinstance(handler, type) and issubclass(handler, VeriClientError):
                raise handler()
            handler(response_json)

        raise ValueError(response_json.get("error", "Unknown error"))

    def _handle_document_not_found(self, response_json: dict) -> None:
        document_id = response_json.get("id", "unknown")
        raise DocumentNotFoundError(document_id)

    def _handle_signature_request_not_found(self, response_json: dict) -> None:
        request_id = response_json.get("id", "unknown")
        raise SignatureRequestNotFoundError(request_id)

    def _handle_signature_not_found(self, response_json: dict) -> None:
        signature_id = response_json.get("id", "unknown")
        raise SignatureNotFoundError(signature_id)

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns:
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=EsignEndpoints.ALIVE.value)
        accepted_status_code = 204
        return response.status_code == accepted_status_code

    def get_library_documents(self) -> list[LibraryDocumentOutput]:
        """Get all library documents.

        Returns:
            List of library documents

        """
        response = self._get(endpoint=EsignEndpoints.LIBRARY_DOCUMENTS.value)
        data = response.json()
        return [LibraryDocumentOutput(status_code=response.status_code, **item) for item in data.get("items", [])]

    def get_library_document(self, library_document_id: str) -> LibraryDocumentOutput:
        """Get a specific library document.

        Args:
            library_document_id: ID of the document to retrieve

        Returns:
            The library document

        Raises:
            DocumentNotFoundError: If the document is not found

        """
        endpoint = EsignEndpoints.LIBRARY_DOCUMENTS_ID.value.replace(
            "<library_document_id>", library_document_id,
        )
        response = self._get(endpoint=endpoint)
        return LibraryDocumentOutput(status_code=response.status_code, **response.json())

    def create_library_document(self, document: LibraryDocumentInput) -> LibraryDocumentOutput:
        """Create a new library document.

        Args:
            document: The document data to create

        Returns:
            The created library document

        Raises:
            InvalidDocumentError: If the document is invalid

        """
        files = [(
            "file", ("esign_example.pdf", document.file, "application/pdf"),
        )]
        data = {
            "name": document.name,
        }

        response = self._post(
            endpoint=EsignEndpoints.LIBRARY_DOCUMENTS.value,
            data=data,
            files=files,
        )
        return LibraryDocumentOutput(status_code=response.status_code, **response.json())

    def create_signature_request(self, signature_request: SignatureRequestInput) -> SignatureRequestOutput:
        """Create a new signature request.

        Args:
            signature_request: The signature request data

        Returns:
            The created signature request

        Raises:
            InvalidDocumentError: If a document is invalid
            DocumentNotFoundError: If a document is not found

        """
        data = {
            "title": signature_request.title,
            "type": signature_request.type,
            "signers": json.dumps([signer.model_dump() for signer in signature_request.signers]),
            "library_document_ids": json.dumps([str(doc_id) for doc_id in signature_request.library_document_ids]),
            "ready": signature_request.ready,
        }

        response = self._post(
            endpoint=EsignEndpoints.SIGNATURE_REQUEST.value,
            data=data,
        )
        return SignatureRequestOutput(status_code=response.status_code, **response.json())

    def send_signature_request(self, signature_request_id: str) -> SignatureRequestOutput:
        """Send a signature request to signers.

        Args:
            signature_request_id: ID of the signature request to send

        Returns:
            The updated signature request

        Raises:
            SignatureRequestNotFoundError: If the signature request is not found

        """
        endpoint = EsignEndpoints.SIGNATURE_REQUEST_SENT.value.replace(
            "<signature_request_id>", signature_request_id,
        )
        response = self._post(endpoint=endpoint)
        return SignatureRequestOutput(status_code=response.status_code, **response.json())

    def get_next_signature(self, signature_request_id: str) -> SignatureOutput:
        """Get the next signature in a signature request.

        Args:
            signature_request_id: ID of the signature request

        Returns:
            The next signature

        Raises:
            SignatureRequestNotFoundError: If the signature request is not found
            SignatureNotFoundError: If no next signature is found

        """
        endpoint = EsignEndpoints.SIGNATURE_NEXT.value.replace(
            "<signature_request_id>", signature_request_id,
        )
        response = self._get(endpoint=endpoint)
        status = response.json().get("status_code")
        return SignatureOutput(status=status, **response.json())

    def sign_document(self, signature_request_id: str, signature_id: str, signature: SignatureInput) -> SignatureOutput:
        """Sign a document.

        Args:
            signature_request_id: ID of the signature request
            signature_id: ID of the signature
            signature: The signature data

        Returns:
            The updated signature

        Raises:
            SignatureRequestNotFoundError: If the signature request is not found
            SignatureNotFoundError: If the signature is not found
            InvalidSignatureError: If the signature is invalid

        """
        endpoint = EsignEndpoints.SIGNATURE_SIGN.value.replace(
            "<signature_request_id>", signature_request_id,
        ).replace(
            "<signature_id>", signature_id,
        )

        data = {
            "name_or_initials": signature.name_or_initials,
        }

        files = {}
        if signature.selfie:
            selfie_data = get_virtual_file(signature.selfie)
            files = {
                "selfie": ("selfie", selfie_data, "image/jpeg"),
            }

        response = self._post(
            endpoint=endpoint,
            data=data,
            files=files if files else None,
        )
        return SignatureOutput(**response.json())

    def finish_signature(self, signature_request_id: str) -> SignatureOutput:
        """Finish a signature process.

        Args:
            signature_request_id: ID of the signature request
            signature_id: ID of the signature

        Returns:
            The updated signature

        Raises:
            SignatureRequestNotFoundError: If the signature request is not found
            SignatureNotFoundError: If the signature is not found

        """
        endpoint = EsignEndpoints.SIGNATURE_FINISH.value.replace(
            "<signature_request_id>", signature_request_id,
        )
        response = self._post(endpoint=endpoint)
        status = response.json().get("status_code")
        return SignatureOutput(status=status, **response.json())

    def get_signature_request_files(self, signature_request_id: str) -> bytes:
        """Get files associated with a signature request.

        Args:
            signature_request_id: ID of the signature request

        Returns:
            The file content

        Raises:
            SignatureRequestNotFoundError: If the signature request is not found

        """
        endpoint = EsignEndpoints.SIGNATURE_REQUEST_FILES.value.replace(
            "<signature_request_id>", signature_request_id,
        )
        response = self._get(endpoint=endpoint)
        return response.content
