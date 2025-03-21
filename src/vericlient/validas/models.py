"""Module to define the models for the Daspeak API."""
# ruff: noqa: N805, D102, ANN201

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

class ValidasResponse(BaseModel):
    """Base class for the vali-Das API responses.

    Attributes:
        validation_id: Unique identifier for the validation process
        status: Current status of the validation

    """
    version: str
    status_code: int

# Input model - Para los path parameters
class ValidationIdInput(BaseModel):
    """Input model for validation ID parameters."""
    validation_id: str

class CreateValidation(ValidasResponse):
    """Response model for creating a new validation.

    Attributes:
        data: Contains the generated validation_id

    """
    data: dict[str, str]  # {"id": "generated-id"}

class ValidationDataResponse(ValidasResponse):
    """Response model for retrieving validation data.

    Attributes:
        data: Contains the validation data including createdAt date in GMT + CET/CEST format

    """
    data: dict[str, Any]  # Contendrá los datos de la validación

class DocumentValidationInput(BaseModel):
    """Input class for document validation.

    Attributes:
        obverse: The obverse (front) image of the document in binary format
        reverse: The reverse (back) image of the document in binary format, optional
        document_type: The type of document, country, or country+document group
        service_mode: The working mode for processing (OCR or validation)
        scores_configuration: Optional configuration for score calculation modifiers
        support_nfc: Optional flag indicating if the user's device supports NFC

    """
    obverse: str | bytes = Field(..., description="Obverse Document image as binary")
    reverse: str | bytes | None = Field(None, description="Reverse Document image as binary")
    document_type: str = Field(..., description="Document type, country, or document group")
    service_mode: str = Field("validation", description="Working mode: 'ocr' or 'validation'")
    scores_configuration: dict[str, Any] | None = Field(None, description="Modifiers for score calculations")
    support_nfc: bool | None = Field(None, description="Indicates if device supports NFC")

class DocumentValidationOutput(ValidasResponse):
    """Output class for document validation.

    Attributes:
        version: The version of the API
        status_code: The status code of the response
        data: Object containing validation results

    """
    data: dict[str, Any] = Field(..., description="Document validation results data")

class SelfieInput(BaseModel):
    """Input class for the validation selfie endpoint.

    Attributes:
        image: The selfie image as binary data, required
        image_alive: Optional smiling selfie image for liveness verification
        antispoofing: Whether to perform antispoofing verification

    """
    image: str | bytes = Field(..., description="Selfie image as binary data")
    image_alive: str | bytes | None = Field(None, description="Smiling selfie image for liveness verification")
    antispoofing: Literal["True", "yes", "False", "no"] | None = Field(
        None,
        description="Indication that antispoofing verification is desired",
    )

    @field_validator("image", "image_alive")
    def must_be_str_or_bytes(cls, value: object) -> str | bytes:
        if value is not None and not isinstance(value, (str, bytes)):
            error_msg = "image must be a string or a bytes object"
            raise TypeError(error_msg)
        return value

    @field_validator("antispoofing")
    def validate_antispoofing(cls, value: str | None) -> str | None:
        if value is not None and value not in ["True", "yes", "False", "no"]:
            error_msg = "antispoofing must be one of: 'True', 'yes', 'False', 'no'"
            raise ValueError(error_msg)
        return value

    class Config:
        arbitrary_types_allowed = True

class SelfieOutput(ValidasResponse):
    """Output class for the validation selfie endpoint.

    Attributes:
        version: The version of the API
        status_code: The status code of the response
        data: The response data including selfie validation results

    """
    data: dict[str, Any] = Field(..., description="Selfie validation results data")

class ChallengeInput(BaseModel):
    """Input model for challenge generation.

    Attributes:
        type: The type of challenge ("selfie-alive-pro"). Optional, defaults to selfie-alive-pro.
        length: Desired length of the challenge (1-6). Default is 2.
        expiration: Challenge expiration time in seconds. Default is 1800.

    """
    type: str = Field(default="selfie-alive-pro", description="Type of challenge")
    length: str = Field(default="2", description="Length of challenge (1-6)")
    expiration: int = Field(default=1800, description="Expiration time in seconds")

    @field_validator("length")
    def validate_length(cls, value: str) -> str:
        try:
            length = int(value)
            if not 1 <= length <= 6:
                error_msg = "Length must be between 1 and 6"
                raise ValueError(error_msg)
        except ValueError as e:
            error_msg = f"Invalid length value: {e}"
            raise ValueError(error_msg) from e
        return value

class ChallengeOutput(ValidasResponse):
    """Output model for challenge generation.

    Attributes:
        data: Contains the challenge data

    """
    data: dict[str, Any] = Field(..., description="Challenge data")

class VideoChallengeInput(BaseModel):
    """Input model for video challenge submission.

    Attributes:
        selfie: Selfie image file (binary)
        video: Video challenge file (binary)
        annotations: WebVTT format annotations file (binary)
        videoFrames: Optional video frames parameters when not uploading full video
        audio: Optional base64 encoded audio file (mp3)

    """
    selfie: str | bytes = Field(..., description="Selfie image as binary")
    video: str | bytes = Field(..., description="Video challenge as binary")
    annotations: str | bytes = Field(..., description="WebVTT format annotations file")
    videoFrames: dict[str, Any] | None = Field(None, description="Video frames parameters")
    audio: str | None = Field(None, description="Base64 encoded audio file (mp3)")

    @field_validator("selfie", "video", "annotations")
    def must_be_str_or_bytes(cls, value: object) -> str | bytes:
        if not isinstance(value, (str, bytes)):
            error_msg = "File must be a string path or bytes"
            raise TypeError(error_msg)
        return value

class VideoChallengeOutput(ValidasResponse):
    """Output model for video challenge submission.

    Attributes:
        data: Contains the response data from the video challenge submission

    """
    data: dict[str, Any] = Field(..., description="Video challenge response data")
