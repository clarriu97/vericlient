"""Module to define the models for the VCSP API."""
# ruff: noqa: N805, D102, ANN201

from pydantic import BaseModel, field_validator


class VcspResponse(BaseModel):
    """Base class for the VCSP API responses.

    Attributes:
        status_code: The status code of the response

    """

    status_code: int


class Sample(BaseModel):
    """Base class for the Sample.

    Attributes:
        valid_from: The date from which the sample is valid
        valid_until: The date until which the sample is valid
        type: The type of the sample, e.g. "voice", "face"
        content_type: The content type of the sample, e.g. "audio/wav", "image/jpeg"
        analysis: The analysis of the sample

    """

    valid_from: str
    valid_until: str
    type: str
    content_type: str
    analysis: dict


class Applicant(BaseModel):
    """Base class for the Applicant.

    Attributes:
        subject_id: The subject_id of the applicant (optional)
        credential_configuration_urn: The credential configuration urn
        tags: The tags of the applicant
        claims: The claims of the applicant
        assurance_method_urn: The assurance method urn
        assurance: The assurance of the applicant

    """

    subject_id: str = None
    credential_configuration_urn: str
    tags: list[str] = None
    claims: dict = None
    assurance_method_urn: str
    assurance: dict


class EnrollmentInput(BaseModel):
    """Input class for the enrollment endpoint.

    Attributes:
        sample: The sample to generate the credential with.
            It can be a path to a file or a bytes object
            with the audio content
        applicant: The applicant to enroll

    """

    sample: str | bytes
    applicant: Applicant

    @field_validator("sample")
    def must_be_str_or_bytes(cls, value: object):
        if not isinstance(value, (str, bytes)):
            error = "sample must be a string or a bytes object"
            raise TypeError(error)
        return value

    class Config:
        arbitrary_types_allowed = True


class EnrollmentOutput(BaseModel):
    """Output class for the enrollment endpoint.

    Attributes:
        credential_id: The credential_id of the applicant
        account_id: The account_id of the applicant

    """

    credential_id: str
    account_id: str


class SubjectInput(BaseModel):
    """Input class to define a subject.

    Attributes:
        subject_id: The subject_id of the applicant

    """

    subject_id: str


class CredentialInput(BaseModel):
    """Input class to define a credential.

    Attributes:
        credential_id: The credential_id of the applicant

    """

    credential_id: str


class DeleteSubjectInput(SubjectInput):
    """Input class for the delete account endpoint.

    Attributes:
        subject_id: The account_id to delete

    """


class DeleteCredentialInput(SubjectInput, CredentialInput):
    """Input class for the delete credential endpoint.

    Attributes:
        credential_id: The credential_id to delete
        subject_id: The subject from which the credential will be deleted

    """


class GetAccountInput(SubjectInput):
    """Input class for the get account endpoint.

    Attributes:
        subject_id: The account_id to get

    """


class GetCredentialInput(SubjectInput, CredentialInput):
    """Input class for the get a specific credential endpoint.

    Attributes:
        subject_id: The subject_id to get the credential from
        credential_id: The credential_id to get

    """


class GetCredentialOutput(VcspResponse):
    """Output class for the get credential endpoint.

    Attributes:
        sample: The sample of the applicant
        groups: The groups of the applicant
        issuer: The issuer
        id: The id of the applicant
        updated_at: The updated_at date
        created_at: The created_at date
        valid_from: The valid_from date
        valid_until: The valid_until date
        credential_configuration_urn: The credential_configuration_urn
        tags: The tags of the applicant
        claims: The claims of the applicant

    """

    sample: Sample
    groups: list[str]
    issuer: str
    id: str
    updated_at: str
    created_at: str
    valid_from: str
    valid_until: str
    credential_configuration_urn: str
    tags: list[str]
    claims: dict


class GetAccountOutput(VcspResponse):
    """Output class for the get account endpoint.

    Attributes:
        credentials: The credentials of the applicant
        updated_at: The updated_at date
        created_at: The created_at date
        subject_id: The subject_id of the applicant

    """

    credentials: list[GetCredentialOutput]
    updated_at: str
    created_at: str
    subject_id: str
