"""Module to define the models for the Daspeak API."""
# ruff: noqa: N805, D102, ANN201

from pydantic import BaseModel, field_validator


class DaspeakResponse(BaseModel):
    """Base class for the Daspeak API responses.

    Attributes:
        version: The version of the API
        status_code: The status code of the response

    """

    version: str
    status_code: int


class ModelsOutput(DaspeakResponse):
    """Output class for the get models endpoint.

    Attributes:
        models: The available models in the service

    """

    models: list


class GenerateCredentialInput(BaseModel):
    """Input class for the generate credential endpoint.

    Attributes:
        audio: The audio to generate the credential with.
            It can be a path to a file or a bytes object
            with the audio content
        hash: The hash of the biometrics model to use
        channel: The `nchannel` of the audio if it is stereo
        calibration: The calibration to use

    """

    audio: str | bytes
    hash: str
    channel: int = 1
    calibration: str = "telephone-channel"

    @field_validator("audio")
    def must_be_str_or_bytes(cls, value: object):
        if not isinstance(value, (str, bytes)):
            error = "audio must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class ModelMetadata(BaseModel):
    """Metadata of the model used to generate the credential.

    Attributes:
        hash: The hash of the model
        mode: The mode of the model

    """

    hash: str
    mode: str


class GenerateCredentialOutput(DaspeakResponse):
    """Output class for the generate credential endpoint.

    Attributes:
        model: The model used to generate the credential
        credential: The generated credential
        authenticity: The authenticity of the audio sample used
        input_audio_duration: The duration of the input audio
        net_speech_duration: The duration of the speech in the audio

    """

    model: ModelMetadata
    credential: str
    authenticity: float
    input_audio_duration: float
    net_speech_duration: float

    @field_validator("authenticity")
    def round_authenticity(cls, value: float) -> float:
        return round(value, 3)


class CompareInput(BaseModel):
    """Base class for the similarity inputs.

    Attributes:
        calibration: The calibration to use

    """

    calibration: str = "telephone-channel"


class CompareOutput(DaspeakResponse):
    """Base class for the similarity outputs.

    Attributes:
        score: The similarity score between the two inputs

    """

    score: float

    @field_validator("score")
    def round_value(cls, value: float) -> float:
        return round(value, 3)


class CompareCredential2CredentialInput(CompareInput):
    """Input class for the similarity credential to credential endpoint.

    Attributes:
        credential_reference: The reference credential
        credential_to_evaluate: The credential to evaluate
        calibration: The calibration to use

    """

    credential_reference: str
    credential_to_evaluate: str


class CompareCredential2CredentialOutput(CompareOutput):
    """Output class for the similarity credential to credential endpoint.

    Attributes:
        calibration: The calibration used

    """

    calibration: str


class CompareCredential2AudioInput(CompareInput):
    """Input class for the similarity credential to audio endpoint.

    Attributes:
        credential_reference: The reference credential
        audio_to_evaluate: The audio to evaluate.
            It can be a path to a file or a bytes object
            with the audio content
        channel: The `nchannel` of the audio if it is stereo

    """

    credential_reference: str
    audio_to_evaluate: str | bytes
    channel: int = 1

    @field_validator("audio_to_evaluate")
    def must_be_str_or_bytes(cls, value: object):
        if not isinstance(value, (str, bytes)):
            error = "audio must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class CompareCredential2AudioOutput(CompareOutput):
    """Output class for the similarity credential to audio endpoint.

    Attributes:
        model: The model used to generate the credential
        calibration: The calibration used
        authenticity_to_evaluate: The authenticity of the audio sample used
        input_audio_duration: The duration of the input audio
        net_speech_duration: The duration of the speech in the audio

    """

    model: ModelMetadata
    calibration: str
    authenticity_to_evaluate: float
    input_audio_duration_to_evaluate: float
    net_speech_duration_to_evaluate: float

    @field_validator("authenticity_to_evaluate")
    def round_value(cls, value: float) -> float:
        return round(value, 3)


class CompareAudio2AudioInput(CompareInput):
    """Input class for the similarity audio to audio endpoint.

    Attributes:
        audio_reference: The reference audio.
            It can be a path to a file or a bytes object
            with the audio content
        audio_to_evaluate: The audio to evaluate.
            It can be a path to a file or a bytes object
            with the audio content
        channel_reference: The `nchannel` of the reference audio if it is stereo
        channel_to_evaluate: The `nchannel` of the audio to evaluate if it is stereo

    """

    audio_reference: str | bytes
    audio_to_evaluate: str | bytes
    channel_reference: int = 1
    channel_to_evaluate: int = 1

    @field_validator("audio_reference", "audio_to_evaluate")
    def audio_ref_must_be_str_or_bytes(cls, value: object):
        if not isinstance(value, (str, bytes)):
            error = "audio must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class CompareAudio2AudioOutput(CompareOutput):
    """Output class for the similarity audio to audio endpoint.

    Attributes:
        model: The model used to generate the credential
        calibration: The calibration used
        authenticity_reference: The authenticity of the reference audio sample
        authenticity_to_evaluate: The authenticity of the audio to evaluate
        input_audio_duration_reference: The duration of the reference audio
        input_audio_duration_to_evaluate: The duration of the audio to evaluate
        net_speech_duration_reference: The duration of the speech in the reference audio
        net_speech_duration_to_evaluate: The duration of the speech in the audio to evaluate

    """

    model: ModelMetadata
    calibration: str
    authenticity_reference: float
    authenticity_to_evaluate: float
    input_audio_duration_reference: float
    input_audio_duration_to_evaluate: float
    net_speech_duration_reference: float
    net_speech_duration_to_evaluate: float

    @field_validator("authenticity_reference", "authenticity_to_evaluate")
    def round_value(cls, value: float) -> float:
        return round(value, 3)


class CompareAudio2CredentialsInput(CompareInput):
    """Input class for the identification audio to credentials endpoint.

    Attributes:
        audio_reference: The audio to evaluate.
            It can be a path to a file or a bytes object
            with the audio content
        credential_list: The credentials to compare the audio with.
            The list contains touples with two strings: the id and the credential
        channel: The `nchannel` of the audio if it is stereo

    """

    audio_reference: str | bytes
    credential_list: list[tuple[str, str]]
    channel: int = 1

    @field_validator("audio_reference")
    def must_be_str_or_bytes(cls, value: object):
        if not isinstance(value, (str, bytes)):
            error = "audio must be a string or a bytes object"
            raise TypeError(error)
        return value

    @field_validator("credential_list")
    def validate_and_build_list_format(cls, value: list):
        if not value:
            error = "credential_list must not be empty"
            raise ValueError(error)
        error = "credential_list must contain touples with two strings"
        n_items = 2
        for item in value:
            if not isinstance(item, tuple) or len(item) != n_items:
                raise ValueError(error)
            if not all(isinstance(i, str) for i in item):
                raise ValueError(error)
        return [{"id": item[0], "credential": item[1]} for item in value]

    class Config:
        arbitrary_types_allowed = True


class CompareAudio2CredentialsOutput(DaspeakResponse):
    """Output class for the identification audio to credentials endpoint.

    Attributes:
        result: The result of the identification, a dictionary with the "id" and the "score"
            of the best match
        scores: The whole list of scores for each credential.
            The list contains dictionaries with two keys (and values): "id" and "score"
        calibration: The calibration used
        model: The model used to generate the credential
        authenticity_reference: The authenticity of the reference audio sample
        input_audio_duration_reference: The duration of the input audio
        net_speech_duration_reference: The duration of the speech in the audio

    """

    result: dict
    scores: list[dict]
    calibration: str
    model: ModelMetadata
    authenticity_reference: float
    input_audio_duration_reference: float
    net_speech_duration_reference: float

    @field_validator("authenticity_reference")
    def round_value(cls, value: float) -> float:
        return round(value, 3)


class CompareCredential2CredentialsInput(CompareInput):
    """Input class for the identification credential to credentials endpoint.

    Attributes:
        credential_reference: The reference credential
        credential_list: The credentials to compare the audio with.
            The list contains touples with two strings: the id and the credential

    """

    credential_reference: str
    credential_list: list[tuple[str, str]]

    @field_validator("credential_list")
    def validate_and_build_list_format(cls, value: list):
        if not value:
            error = "credential_list must not be empty"
            raise ValueError(error)
        error = "credential_list must contain touples with two strings"
        n_items = 2
        for item in value:
            if not isinstance(item, tuple) or len(item) != n_items:
                raise ValueError(error)
            if not all(isinstance(i, str) for i in item):
                raise ValueError(error)
        return [{"id": item[0], "credential": item[1]} for item in value]


class CompareCredential2CredentialsOutput(DaspeakResponse):
    """Output class for the identification credential to credentials endpoint.

    Attributes:
        result: The result of the identification, a dictionary with the "id" and the "score"
            of the best match
        scores: The whole list of scores for each credential.
            The list contains dictionaries with two keys (and values): "id" and "score"
        calibration: The calibration used
        model: The model used to generate the credential

    """

    result: dict
    scores: list[dict]
    calibration: str
