"""Module to define the endpoints for VCSP API."""
from enum import Enum

from vericlient.endpoints import Endpoints


class VcspEndpoints(Enum):   # noqa: D101
    ALIVE = Endpoints.ALIVE.value
    ENROLLMENTS = "enrollments"
    ENROLLMENTS_BATCH = "enrollments/batch"
    ACCOUNTS = "accounts/<subject_id>"
    CREDENTIALS = "accounts/<subject_id>/credentials"
    CREDENTIAL_ID = "accounts/<subject_id>/credentials/<credential_id>"
    GROUPS = "groups"
    GROUP_NAME = "groups/<group_name>"
    MATCHINGS = "matchings"
    CREDENTIAL_CONFIGURATIONS = "credential_configurations"
    CREDENTIAL_CONFIGURATION_URN = "credential_configurations/<urn>"
    ASSURANCE_METHODS = "assurance_methods"
    ASSURANCE_METHOD_URN = "assurance_methods/<urn>"
    TAGS = "tags"
    TAGS_NAME = "tags/<tag_name>"
    TASKS = "tasks"
    TASK_ID = "tasks/<task_id>"
    TASK_RESULT = "tasks/<task_id>/result"
