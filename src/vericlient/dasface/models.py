"""Module to define the models for the das-Face API.

Note the naming: das-Face fields are camelCase on the wire, where das-Peak and VCSP use
snake_case. The models use Python names and alias them, so callers write
`anchor_image` and the service receives `anchorImage`.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class BiometricsModel(BaseModel):
    """One biometrics model the service offers.

    Attributes:
        hash: The hash that identifies the model
        mode: The mode it runs in, such as `default-mode` or `document-mode`
        tag: Its release tag
        methods: The biometric methods it implements
        length: The length of the credentials it produces

    """

    hash: str
    mode: str
    tag: str
    methods: list[str]
    length: int


class ModelsOutput(BaseModel):
    """Output class for the models endpoint.

    Attributes:
        models: Every model the service offers, one entry per hash and mode

    """

    models: list[BiometricsModel]


class ModelMetadata(BaseModel):
    """Metadata identifying the model a credential was generated with.

    Attributes:
        hash: The hash of the model
        mode: The mode it ran in
        tag: Its release tag, when the service reports one

    """

    hash: str
    mode: str
    tag: str | None = None


class GenerateCredentialInput(BaseModel):
    """Input class for generating a credential from a photo.

    The model is part of the credential: two credentials only compare if they were
    generated with the same one. The service does not pick a model on its own, so `hash`
    and `mode` are required. Take them from `get_models()`.

    The only exception is the INE Mexico variant, which does have a default-model form:
    with `inemex` set, leaving `hash` and `mode` out uses it.

    Attributes:
        image: The photo, as a path or as bytes
        hash: The hash of the model to use, from `get_models()`
        mode: The mode to use, from `get_models()`
        inemex: Use the INE Mexico variant of the endpoint. It needs a specific agreement
            with Veridas

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: str | bytes
    hash: str | None = None
    mode: str | None = None
    inemex: bool = False

    @field_validator("image")
    def image_must_be_str_or_bytes(cls, value: object) -> object:  # noqa: N805
        """Reject anything that is neither a path nor bytes."""
        if not isinstance(value, (str, bytes)):
            error = "image must be a string or a bytes object"
            raise TypeError(error)
        return value

    @model_validator(mode="after")
    def model_must_be_named_in_full(self) -> "GenerateCredentialInput":
        """Require hash and mode together, and require them at all outside INE Mexico.

        A model key is the pair, so half of it is always an error. Only the INE Mexico
        endpoint has a default-model form, so everywhere else the pair is mandatory:
        there is no endpoint that lets the service choose.

        A model validator rather than a field one, because pydantic does not run field
        validators over a field left at its default, which is exactly the case being caught.
        """
        if bool(self.hash) != bool(self.mode):
            error = "hash and mode go together: give both or neither"
            raise ValueError(error)
        if not self.inemex and not self.hash:
            error = "hash and mode are required: take them from get_models()"
            raise ValueError(error)
        return self


class GenerateCredentialOutput(BaseModel):
    """Output class for generating a credential from a photo.

    Attributes:
        credential: The biometric representation of the face
        model: The model it was generated with

    """

    credential: str
    model: ModelMetadata


class GetModelMetadataFromCredentialInput(BaseModel):
    """Input class for reading which model produced a credential.

    Attributes:
        credential: The credential to inspect

    """

    credential: str


class GetModelMetadataFromCredentialOutput(BaseModel):
    """Output class for reading which model produced a credential.

    Attributes:
        metadata: The model the credential was generated with

    """

    metadata: ModelMetadata


class VerifyPhotoInput(BaseModel):
    """Input class for comparing two photos.

    Attributes:
        anchor_image: The reference photo, as a path or as bytes
        target_image: The photo to evaluate, as a path or as bytes
        mode: The model mode to use, such as `document-mode`. The service picks its default
            when omitted

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    anchor_image: str | bytes
    target_image: str | bytes
    mode: str | None = None


class VerifyVideoInput(BaseModel):
    """Input class for comparing a photo against a video.

    Attributes:
        anchor_image: The reference photo, as a path or as bytes
        target_video: The video to evaluate, as a path or as bytes

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    anchor_image: str | bytes
    target_video: str | bytes


class VerifyCredentialInput(BaseModel):
    """Input class for comparing a photo against a stored credential.

    Attributes:
        anchor_image: The photo, as a path or as bytes
        target_credential: The credential to compare it with

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    anchor_image: str | bytes
    target_credential: str


class VerificationOutput(BaseModel):
    """Output class for a verification.

    Attributes:
        confidence: How confident the service is that both faces belong to the same person,
            from 0 to 1

    """

    confidence: float


class PhotoAuthenticityInput(BaseModel):
    """Input class for checking whether a selfie is a genuine capture.

    Attributes:
        image: The selfie to analyse, as a path or as bytes

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: str | bytes


class PhotoAuthenticityOutput(BaseModel):
    """Output class for a photo authenticity check.

    Attributes:
        confidence: How confident the service is that the photo is a genuine capture rather
            than a photo of a screen or a print, from 0 to 1

    """

    confidence: float


class VideoAuthenticityInput(BaseModel):
    """Input class for checking a video's authenticity and who is in it.

    Attributes:
        anchor_image: The photo of the person the video should show, as a path or as bytes
        target_video: The video to analyse, as a path or as bytes

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    anchor_image: str | bytes
    target_video: str | bytes


class VideoAuthenticityOutput(BaseModel):
    """Output class for a video authenticity check.

    Both figures matter, and they answer different questions: a genuine recording of the
    wrong person scores high on one and low on the other.

    Attributes:
        authenticity: How confident the service is that the video is a genuine recording
        similarity: How closely the face in the video matches the anchor photo

    """

    authenticity: float
    similarity: float


class SequentialChallengeInput(BaseModel):
    """Input class for requesting a sequential liveness challenge.

    Attributes:
        length: How many actions the challenge asks for, from 1 to 6. The service defaults
            to 2, which it describes as standard security, and 6 as high security
        expiration: How long the challenge stays valid, in seconds, from 300 to 1800. The
            service defaults to 1800

    """

    length: int | None = None
    expiration: int | None = None


class ChallengeAction(BaseModel):
    """One action the subject is asked to perform.

    Attributes:
        name: The name the annotations refer to this action by, such as `action-0`
        action_class: What kind of action it is, such as `move-head-and-back`. Named this way
            because `class` is a Python keyword; the token itself calls it `class`
        parameters: The details of the action, such as `{"direction": "right"}`

    """

    name: str
    action_class: str
    parameters: dict


class SequentialChallengeOutput(BaseModel):
    """Output class for a sequential liveness challenge.

    The service answers with a signed token rather than JSON. Pass `token` on unchanged: the
    capture SDK needs it, and so does `analyse_challenge_response`. The rest of the fields
    are read from inside it, because a caller has to know which actions to prompt for.

    Attributes:
        token: The JWS token, exactly as the service returned it
        id: The identifier of this challenge
        timestamp: When the challenge was issued
        expires: When it stops being accepted
        actions: The actions to perform, in order

    """

    token: str
    id: str
    timestamp: datetime
    expires: datetime
    actions: list[ChallengeAction]


class ChallengeAnalysisInput(BaseModel):
    """Input class for analysing the recording of a challenge.

    Attributes:
        token: The token from `generate_sequential_challenge`, unchanged
        annotations: The SDK's WebVTT annotations of the recording, as a path or as bytes.
            A `str` is read as a path, so pass in-memory text as `text.encode()`
        anchor_image: The photo of the person the recording should show, as a path or as bytes
        target_video: The recording of the challenge, as a path or as bytes

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    token: str
    annotations: str | bytes
    anchor_image: str | bytes
    target_video: str | bytes


class ChallengeError(BaseModel):
    """One reason the analysis could not produce a confidence.

    Attributes:
        code: The error code, such as `FaceTooSmallForIAS`
        message: What the service said about it

    """

    code: str
    message: str


class ChallengeAnalysisOutput(BaseModel):
    """Output class for the analysis of a challenge recording.

    This endpoint reports its failures in a successful response rather than as an error
    status, which no other das-Face endpoint does. A `confidence` of `None` means the
    analysis could not be completed and `errors` says why — a face too small to analyse
    comes back here, where every other endpoint raises.

    Attributes:
        confidence: How confident the service is that the recording is a genuine response to
            the challenge by the person in the anchor photo, from 0 to 1, or `None` if it
            could not tell
        errors: What went wrong, empty when nothing did

    """

    confidence: float | None
    errors: list[ChallengeError]
