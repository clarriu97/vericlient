"""Module to define the models for the Daspeak API"""
from typing import Union
from io import BytesIO

from pydantic import BaseModel, field_validator


class DaspeakResponse(BaseModel):
    version: str
    status_code: int


class ModelsOutput(DaspeakResponse):
    models: list


class ModelsMetadataInput(BaseModel):
    hash: str


class ModelsMetadata(BaseModel):
    hash: str
    description: str


class ModelsMetadataOutput(DaspeakResponse):
    metadata: ModelsMetadata


class ModelsCalibrationInput(BaseModel):
    hash: str


class ModelsCalibrationOutput(DaspeakResponse):
    hash: str
    calibrations: list


class ModelsMetadataFromCredentialInput(BaseModel):
    credential: str


class ModelsMetadataFromCredentialOutput(DaspeakResponse):
    metadata: ModelsMetadata


class ModelsHashCredentialWavInput(BaseModel):
    audio: Union[str, BytesIO]
    hash: str
    channel: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio")
    def must_be_str_or_bytesio(cls, value):
        if not isinstance(value, (str, BytesIO)):
            raise ValueError("audio must be a string or a BytesIO object")

    class Config:
        arbitrary_types_allowed = True


class ModelMetadata(BaseModel):
    hash: str
    mode: str


class ModelsHashCredentialWavOutput(DaspeakResponse):
    model: ModelMetadata
    credential: str
    authenticity: float
    input_audio_duration: float
    net_speech_duration: float


class SimilarityCredential2CredentialInput(BaseModel):
    credential_reference: str
    credential_to_evaluate: str
    caliration: str = "telephone-channel"


class SimilarityCredential2CredentialOutput(DaspeakResponse):
    calibration: str
    score: float


class SimilarityCredential2WavInput(BaseModel):
    credential_reference: str
    audio_to_evaluate: Union[str, BytesIO]
    channel: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio_to_evaluate")
    def must_be_str_or_bytesio(cls, value):
        if not isinstance(value, (str, BytesIO)):
            raise ValueError("audio must be a string or a BytesIO object")

    class Config:
        arbitrary_types_allowed = True


class SimilarityCredential2WavOutput(DaspeakResponse):
    score: float
    model: ModelMetadata
    calibration: str
    authenticity_to_evaluate: float
    input_audio_duration: float
    net_speech_duration: float


class SimilarityWav2WavInput(BaseModel):
    audio_reference: Union[str, BytesIO]
    audio_to_evaluate: Union[str, BytesIO]
    channel_reference: int = 1
    channel_to_evaluate: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio_reference")
    def audio_ref_must_be_str_or_bytesio(cls, value):
        if not isinstance(value, (str, BytesIO)):
            raise ValueError("audio must be a string or a BytesIO object")

    @field_validator("audio_to_evaluate")
    def audio_to_eval_must_be_str_or_bytesio(cls, value):
        if not isinstance(value, (str, BytesIO)):
            raise ValueError("audio must be a string or a BytesIO object")

    class Config:
        arbitrary_types_allowed = True


class SimilarityWav2WavOutput(DaspeakResponse):
    score: float
    model: ModelMetadata
    calibration: str
    authenticity_reference: float
    authenticity_to_evaluate: float
    input_audio_duration_reference: float
    input_audio_duration_to_evaluate: float
    net_speech_duration_reference: float
    net_speech_duration_to_evaluate: float


class IdentificationCredential2CredentialInput(BaseModel):
    credential_reference: str
    credentials_list: list
    calibration: str = "telephone-channel"


class IdentificationCredential2CredentialOutput(DaspeakResponse):
    calibration: str
    model: ModelMetadata
    scores: list
