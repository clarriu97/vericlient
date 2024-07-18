"""Module to define the models for the Daspeak API."""
# ruff: noqa: N805, D102, ANN201
from io import BytesIO

from pydantic import BaseModel, field_validator


class DaspeakResponse(BaseModel):
    """Base class for the Daspeak API responses.

    Attributes:
        version: the version of the API
        status_code: the status code of the response

    """

    version: str
    status_code: int


class ModelsOutput(DaspeakResponse):
    """Output class for the get models endpoint.

    Attributes:
        models: the available models in the service

    """

    models: list


class ModelsHashCredentialAudioInput(BaseModel):
    """Input class for the generate credential endpoint.

    Attributes:
        audio: the audio to generate the credential with
        hash: the hash of the biometrics model to use
        channel: the `nchannel` of the audio if it is stereo
        calibration: the calibration to use

    """

    audio: str | BytesIO
    hash: str
    channel: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio")
    def must_be_str_or_bytesio(cls, value: object):
        if not isinstance(value, (str, BytesIO)):
            error = "audio must be a string or a BytesIO object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class ModelMetadata(BaseModel):
    """Metadata of the model used to generate the credential.

    Attributes:
        hash: the hash of the model
        mode: the mode of the model

    """

    hash: str
    mode: str


class ModelsHashCredentialAudioOutput(DaspeakResponse):
    """Output class for the generate credential endpoint.

    Attributes:
        model: the model used to generate the credential
        credential: the generated credential
        authenticity: the authenticity of the audio sample used
        input_audio_duration: the duration of the input audio
        net_speech_duration: the duration of the speech in the audio

    """

    model: ModelMetadata
    credential: str
    authenticity: float
    input_audio_duration: float
    net_speech_duration: float

    @field_validator("authenticity")
    def round_authenticity(cls, value: float) -> float:
        return round(value, 3)


class SimilarityCredential2CredentialInput(BaseModel):
    """Input class for the similarity credential to credential endpoint.

    Attributes:
        credential_reference: the reference credential
        credential_to_evaluate: the credential to evaluate
        calibration: the calibration to use

    """

    credential_reference: str
    credential_to_evaluate: str
    caliration: str = "telephone-channel"


class SimilarityCredential2CredentialOutput(DaspeakResponse):
    """Output class for the similarity credential to credential endpoint.

    Attributes:
        score: the similarity score between the two credentials
        calibration: the calibration used

    """

    calibration: str
    score: float

    @field_validator("score")
    def round_authenticity(cls, value: float) -> float:
        return round(value, 3)


class SimilarityCredential2AudioInput(BaseModel):
    """Input class for the similarity credential to audio endpoint.

    Attributes:
        credential_reference: the reference credential
        audio_to_evaluate: the audio to evaluate
        channel: the `nchannel` of the audio if it is stereo
        calibration: the calibration to use

    """

    credential_reference: str
    audio_to_evaluate: str | BytesIO
    channel: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio_to_evaluate")
    def must_be_str_or_bytesio(cls, value: object):
        if not isinstance(value, (str, BytesIO)):
            error = "audio must be a string or a BytesIO object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class SimilarityCredential2AudioOutput(DaspeakResponse):
    """Output class for the similarity credential to audio endpoint.

    Attributes:
        score: the similarity score between the credential and the audio
        model: the model used to generate the credential
        calibration: the calibration used
        authenticity_to_evaluate: the authenticity of the audio sample used
        input_audio_duration: the duration of the input audio
        net_speech_duration: the duration of the speech in the audio

    """

    score: float
    model: ModelMetadata
    calibration: str
    authenticity_to_evaluate: float
    input_audio_duration_to_evaluate: float
    net_speech_duration_to_evaluate: float

    @field_validator("score", "authenticity_to_evaluate")
    def round_authenticity(cls, value: float) -> float:
        return round(value, 3)


class SimilarityAudio2AudioInput(BaseModel):
    """Input class for the similarity audio to audio endpoint.

    Attributes:
        audio_reference: the reference audio
        audio_to_evaluate: the audio to evaluate
        channel_reference: the `nchannel` of the reference audio if it is stereo
        channel_to_evaluate: the `nchannel` of the audio to evaluate if it is stereo
        calibration: the calibration to use

    """

    audio_reference: str | BytesIO
    audio_to_evaluate: str | BytesIO
    channel_reference: int = 1
    channel_to_evaluate: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio_reference", "audio_to_evaluate")
    def audio_ref_must_be_str_or_bytesio(cls, value: object):
        if not isinstance(value, (str, BytesIO)):
            error = "audio must be a string or a BytesIO object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class SimilarityAudio2AudioOutput(DaspeakResponse):
    """Output class for the similarity audio to audio endpoint.

    Attributes:
        score: the similarity score between the two audios
        model: the model used to generate the credential
        calibration: the calibration used
        authenticity_reference: the authenticity of the reference audio sample
        authenticity_to_evaluate: the authenticity of the audio to evaluate
        input_audio_duration_reference: the duration of the reference audio
        input_audio_duration_to_evaluate: the duration of the audio to evaluate
        net_speech_duration_reference: the duration of the speech in the reference audio
        net_speech_duration_to_evaluate: the duration of the speech in the audio to evaluate

    """

    score: float
    model: ModelMetadata
    calibration: str
    authenticity_reference: float
    authenticity_to_evaluate: float
    input_audio_duration_reference: float
    input_audio_duration_to_evaluate: float
    net_speech_duration_reference: float
    net_speech_duration_to_evaluate: float

    @field_validator("score", "authenticity_reference", "authenticity_to_evaluate")
    def round_authenticity(cls, value: float) -> float:
        return round(value, 3)
