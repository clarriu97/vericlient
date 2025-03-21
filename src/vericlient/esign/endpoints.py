"""Module to define the endpoints for Daspeak API."""
from enum import Enum

from vericlient.endpoints import Endpoints


class EsignEndpoints(Enum):   # noqa: D101
    ALIVE = Endpoints.ALIVE.value
    LIBRARY_DOCUMENTS = "library_documents" # GET
    LIBRARY_DOCUMENTS_ID = "library_documents/<library_document_id>" # GET, PUT, DELETE
    LIBRARY_DOCUMENTS_FILE = "library_documents/<library_document_id>/file" # GET
    LIBRARY_DOCUMENTS_PREVIEW_FILE = "library_documents/<library_document_id>/preview_file" # GET

    SIGNATURE_REQUEST = "signature_request" # GET, POST
    SIGNATURE_REQUEST_VERIFY = "signature_request/verify" # POST
    SIGNATURE_REQUEST_ID = "signature_request/<signature_request_id>" # GET, PUT, DELETE
    SIGNATURE_REQUEST_FILES = "signature_request/<signature_request_id>/files?folder=all" # GET, POST
    SIGNATURE_REQUEST_SENT = "signature_request/<signature_request_id>/sent" # GET
    SIGNATURE_REQUEST_CANCEL = "signature_request/<signature_request_id>/cancel" # POST
    SIGNATURE_REQUEST_SIGNERS = "signature_request/<signature_request_id>/signers" # GET, POST
    SIGNATURE_REQUEST_SIGNERS_ID = "signature_request/<signature_request_id>/signers/<signer_id>" # GET, PUT, DELETE

    SIGNATURE = "signature_request/<signature_request_id>/signatures" # GET, POST
    SIGNATURE_NEXT = "signature_request/<signature_request_id>/signatures/next" # GET
    SIGNATURE_SIGN = "signature_request/<signature_request_id>/signatures/<signature_id>/sign" # POST
    SIGNATURE_FINISH = "signature_request/<signature_request_id>/finish" # POST
    SIGNATURE_DECLINE = "signature_request/<signature_request_id>/signatures/<signature_id>/decline" # POST

    EVENTS = "events" # GET
    EVENTS_ID = "events/<event_id>" # GET
