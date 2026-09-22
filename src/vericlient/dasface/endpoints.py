"""Module to define the endpoints for the das-Face API."""

from enum import Enum

from vericlient.endpoints import Endpoints


class DasfaceEndpoints(Enum):  # noqa: D101
    ALIVE = Endpoints.ALIVE.value
    MODELS = "models"
    MODELS_METADATA_FROM_CREDENTIAL = "models/metadata/from-credential"
    MODEL_CREDENTIAL_PHOTO = "models/<hash>/<mode>/credential/photo"
    INEMEX_DEFAULT_CREDENTIAL_PHOTO = "models/inemex/default-mode/credential/photo"
    INEMEX_MODEL_CREDENTIAL_PHOTO = "inemex/models/<hash>/<mode>/credential/photo"
    VERIFICATION_PHOTO = "verification/photo"
    VERIFICATION_VIDEO = "verification/video"
    VERIFICATION_CREDENTIAL = "verification/credential"
    AUTHENTICITY_PHOTO = "authenticity/photo"
    AUTHENTICITY_VIDEO_PHOTO = "authenticity/video/photo"
    CHALLENGES_GENERATION_SEQUENTIAL = "challenges/generation/sequential"
    CHALLENGES_ANALYSIS_VIDEO_PHOTO = "challenges/analysis/video-photo"
