"""Module to define the models for the das-Face API.

Note the naming: das-Face fields are camelCase on the wire, where das-Peak and VCSP use
snake_case. The models use Python names and alias them, so callers write
`anchor_image` and the service receives `anchorImage`.
"""

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

    Leave `hash` and `mode` out to use the service's current default model, which is the
    usual case; set them to pin a specific one.

    Attributes:
        image: The photo, as a path or as bytes
        hash: The hash of the model to use
        mode: The mode to use. Required when `hash` is given

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: str | bytes
    hash: str | None = None
    mode: str | None = None

    @field_validator("image")
    def image_must_be_str_or_bytes(cls, value: object) -> object:  # noqa: N805
        """Reject anything that is neither a path nor bytes."""
        if not isinstance(value, (str, bytes)):
            error = "image must be a string or a bytes object"
            raise TypeError(error)
        return value

    @model_validator(mode="after")
    def mode_required_with_hash(self) -> "GenerateCredentialInput":
        """Require the mode whenever a hash is given: the model key is both together.

        A model validator rather than a field one, because pydantic does not run field
        validators over a field left at its default, which is exactly the case being caught.
        """
        if self.hash and not self.mode:
            error = "mode is required when hash is given"
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
