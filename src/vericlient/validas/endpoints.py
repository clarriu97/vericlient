"""Module to define the endpoints for vali-DAs API."""
from enum import Enum

from vericlient.endpoints import Endpoints


class ValidasEndpoints(Enum):   # noqa: D101
    ALIVE = Endpoints.ALIVE.value
    
    # Main flow - Document validation
    CREATE_VALIDATION = "validation"
    GET_VALIDATION_DATA = "validation/<validation_id>"
    VALIDATION_CONTEXTUAL_DATA = "validation/<validation_id>/contextual_data"
    VALIDATION_DOCUMENT = "validation/<validation_id>/document"
    VALIDATION_NFC_KEYS = "validation/<validation_id>/nfc_keys_pins"
    VALIDATION_NFC = "validation/<validation_id>/nfc"
    VALIDATION_SELFIE = "validation/<validation_id>/selfie"
    VALIDATION_CHALLENGE = "validation/<validation_id>/challenges/generation"
    VALIDATION_CHALLENGE_VIDEO_PHOTO = "validation/<validation_id>/challenges/video-photo"
    VALIDATION_VIDEO = "validation/<validation_id>/video"
    VALIDATION_IDENTITY_VERIFICATION = "validation/<validation_id>/identity_verification"
    VALIDATION_PEP_AML = "validation/<validation_id>/pep_aml"
    VALIDATION_TIMESTAMP = "validation/<validation_id>/timestamp"
    VALIDATION_OCR = "validation/<validation_id>/ocr"
    VALIDATION_SCORES = "validation/<validation_id>/scores"
    VALIDATION_EVENTS = "validation/<validation_id>/events"
    VALIDATION_CONFIRMATION = "validation/<validation_id>/confirmation"
    VALIDATION_CANCELLATION = "validation/<validation_id>/cancellation"
    VALIDATION_AGE_VERIFICATION = "validation/<validation_id>/age_verification"
    