# VCSP Client usage

Examples for the [VCSP](https://docs.veridas.com/vcsp_echo/cloud/latest/) client. VCSP
stores biometric credentials for you, rather than handing them back to be stored on your
side as das-Peak does.

See [Supported endpoints](../../supported_endpoints.md) for what is covered so far.

## Check if the API is alive

```python
from vericlient import VcspClient

client = VcspClient(apikey="your_api_key")

print(f"Alive: {client.alive()}")
```

## Discover what the subscription allows

Before enrolling anyone you need two URNs: a credential configuration, which says what kind
of credential to create, and an assurance method, which says what the sample has to satisfy.
Both are specific to your subscription, so read them from the service rather than
hardcoding them.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import AssuranceMethodInput

client = VcspClient(apikey="your_api_key")

configurations = client.get_credential_configurations().credential_configurations
print(f"Credential configurations: {configurations}")

methods = client.get_assurance_methods().assurance_methods
print(f"Assurance methods: {methods}")
```

Each assurance method carries a JSON schema describing the values it expects, which is what
goes into the `assurance` field when enrolling:

```python
method = client.get_assurance_method_info(AssuranceMethodInput(urn=methods[0]))
print(method.json_schema.title)
print(method.json_schema.properties)
```

## Enrol a subject

```python
from vericlient import VcspClient
from vericlient.vcsp.models import Applicant, EnrollmentInput

client = VcspClient(apikey="your_api_key")

configuration = next(c for c in client.get_credential_configurations().credential_configurations if "telephone" in c)
method = next(m for m in client.get_assurance_methods().assurance_methods if "enrollment:thresholds" in m)

enrollment = client.enroll_subject(
    EnrollmentInput(
        sample="/path/to/audio.wav",
        applicant=Applicant(
            subject_id="user-1",
            credential_configuration_urn=configuration,
            assurance_method_urn=method,
            assurance={"authenticity_threshold": 0.5},
        ),
    ),
)
print(f"Subject {enrollment.subject_id} now holds credential {enrollment.credential_id}")
```

`subject_id` is optional. Leave it out and VCSP generates one, returned on the response.

### Enrolling from memory

`sample` also takes a `bytes` object. The media type is inferred from the content, but VCSP
answers 500 rather than a 4xx when the declared type does not match what it receives, so set
`content_type` explicitly if the sample is anything unusual:

```python
with open("/path/to/audio.wav", "rb") as f:
    enrollment = client.enroll_subject(
        EnrollmentInput(sample=f.read(), applicant=applicant, content_type="audio/wav"),
    )
```

## Read an account and its credentials

```python
from vericlient import VcspClient
from vericlient.vcsp.models import GetAccountInput, GetCredentialInput, GetCredentialsInput

client = VcspClient(apikey="your_api_key")

account = client.get_account(GetAccountInput(subject_id="user-1"))
print(f"Created at {account.created_at}, {len(account.credentials)} credential(s)")

credentials = client.get_all_subject_credentials(GetCredentialsInput(subject_id="user-1")).credentials
for credential in credentials:
    print(f"{credential.id}: {credential.sample.type}, valid until {credential.valid_until}")

one = client.get_credential(
    GetCredentialInput(subject_id="user-1", credential_id=credentials[0].id),
)
print(one.claims, one.tags)
```

## Delete a credential or a whole account

Deleting an account removes every credential it holds. Both are permanent.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import DeleteAccountInput, DeleteCredentialInput

client = VcspClient(apikey="your_api_key")

client.delete_credential(
    DeleteCredentialInput(subject_id="user-1", credential_id="the-credential-id"),
)
client.delete_account(DeleteAccountInput(subject_id="user-1"))
```

## Handling failures

```python
from vericlient.vcsp.exceptions import AccountNotFoundError, AssuranceValidationError

try:
    client.enroll_subject(enrollment_input)
except AssuranceValidationError:
    print("The sample did not meet the assurance thresholds")

try:
    client.get_account(GetAccountInput(subject_id="does-not-exist"))
except AccountNotFoundError:
    print("No such subject")
```

The full list is in [Error handling](../../errors.md).

## Tags

Tags label credentials so they can be filtered later. A tag must exist before a credential
can carry it, and its name must be `key:value` with alphanumerics only —
`^[a-zA-Z0-9]+:[a-zA-Z0-9]+$`, so `role:employee` is valid and `role-employee` is not.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import CreateTagsInput, DeleteTagInput

client = VcspClient(apikey="your_api_key")

client.create_tags(CreateTagsInput(tags=["role:employee", "region:eu"]))

for tag in client.get_tags().items:
    print(f"{tag.name} (created {tag.created_at})")

client.delete_tag(DeleteTagInput(name="region:eu"))
```

Once a tag exists, pass it when enrolling:

```python
Applicant(
    subject_id="user-1",
    credential_configuration_urn=configuration,
    assurance_method_urn=method,
    assurance={"authenticity_threshold": 0.5},
    tags=["role:employee"],
)
```

## Groups

Groups are how a set of credentials is referred to for 1:N matching. A group name must match
`^[a-zA-Z_][a-zA-Z0-9_]{2,63}$` — letters, digits and underscores, starting with a letter or
an underscore. Hyphens are rejected.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import (
    CreateGroupInput,
    DeleteGroupInput,
    GetGroupInput,
    GetGroupMembersInput,
    GetGroupsInput,
)

client = VcspClient(apikey="your_api_key")
configuration = next(c for c in client.get_credential_configurations().credential_configurations if "voice" in c)

group = client.create_group(
    CreateGroupInput(name="support_agents", credential_configuration_urn=configuration),
)
print(f"{group.name} holds {group.size} credentials, expiring {group.expired_at}")

for g in client.get_groups(GetGroupsInput()).items:
    print(g.name)

members = client.get_group_members(GetGroupMembersInput(name="support_agents"))
print(f"{members.total} members")

client.delete_group(DeleteGroupInput(name="support_agents"))
```

!!! warning "`expired_at` is a duration going in and a date coming out"

    `CreateGroupInput.expired_at` takes an **ISO 8601 duration** — a retention period such as
    `P1Y` or `P30D`, not a date. The service applies it and answers with the resulting
    timestamp in `CreateGroupOutput.expired_at`. Leave it out and credentials are retained
    for five years.

!!! note "Subscriptions cap the number of groups"

    Creating one past the limit raises `GroupsLimitExceededError`. The limit is part of the
    subscription, not something the client controls.
