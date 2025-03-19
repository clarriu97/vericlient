"""Module to define the models for the VCSP API."""
# ruff: noqa: N805, D102, ANN201

from pydantic import BaseModel, Field


class VcspResponse(BaseModel):
    """Base class for the VCSP API responses.

    Attributes:
        status_code: The status code of the response

    """

    status_code: int


class CredentialConfigurationsOutput(VcspResponse):
    """Output class for the credential configurations endpoint.

    Attributes:
        credential_configurations: The credential configurations

    """

    credential_configurations: list[str]


class AssuranceMethodsOutput(VcspResponse):
    """Output class for the assurance methods endpoint.

    Attributes:
        assurance_methods: The assurance methods

    """

    assurance_methods: list[str]


class AssuranceMethodSchema(BaseModel):
    """Schema class for the assurance method.

    Attributes:
        $schema: The schema of the assurance method
        title: The title of the assurance method
        type: The type of the assurance method
        properties: The properties of the assurance method
        required: The required properties of the assurance method
        additionalProperties: Whether additional properties are allowed

    """

    schema: str = Field(alias="$schema")
    title: str
    type: str
    properties: dict
    required: list[str] = None
    additionalProperties: bool      # noqa: N815


class AssuranceMethodInput(BaseModel):
    """Input class for the assurance method endpoint.

    Attributes:
        urn: The urn of the assurance method

    """

    urn: str


class AssuranceMethodOutput(VcspResponse):
    """Output class for the assurance method endpoint.

    Attributes:
        urn: The urn of the assurance method
        schema: The schema of the assurance method

    """

    urn: str
    schema: AssuranceMethodSchema
