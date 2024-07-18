"""Module to define the endpoints for Daspeak API."""
from enum import Enum

from vericlient.endpoints import Endpoints


class DaspeakEndpoints(Enum):   # noqa: D101
    ALIVE = Endpoints.ALIVE.value
    MODELS = "models"
    MODELS_METADATA = "models/metadata"
    MODELS_CALIBRATION = "models/calibration"
    MODELS_METADATA_FROM_CREDENTIAL = "models/metadata/from-credential"
    MODELS_HASH_CREDENTIAL_AUDIO = "models/<hash>/credential/wav"
    SIMILARITY_CREDENTIAL2CREDENTIAL = "similarity/credential2credential"
    SIMILARITY_CREDENTIAL2AUDIO = "similarity/credential2wav"
    SIMILARITY_AUDIO2AUDIO = "similarity/wav2wav"
    IDENTIFICATION_AUDIO2CREDENTIALS = "identification/wav2credentials"
    IDENTIFICATION_CREDENTIAL2CREDENTIALS = "identification/credential2credentials"
