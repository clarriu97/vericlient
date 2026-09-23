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

client = VcspClient(apikey="your_api_key")

configurations = client.get_credential_configurations().credential_configurations
print(f"Credential configurations: {configurations}")

methods = client.get_assurance_methods().assurance_methods
print(f"Assurance methods: {methods}")
```

Each assurance method carries a JSON schema describing the values it expects, which is what
goes into the `assurance` field when enrolling:

```python
method = client.get_assurance_method_info(urn=methods[0])
print(method.json_schema.title)
print(method.json_schema.properties)
```

## Enrol a subject

```python
from vericlient import VcspClient
from vericlient.vcsp.models import Applicant

client = VcspClient(apikey="your_api_key")

configuration = next(c for c in client.get_credential_configurations().credential_configurations if "telephone" in c)
method = next(m for m in client.get_assurance_methods().assurance_methods if "enrollment:thresholds" in m)

enrollment = client.enroll_subject(
    sample="/path/to/audio.wav",
    applicant=Applicant(
        subject_id="user-1",
        credential_configuration_urn=configuration,
        assurance_method_urn=method,
        assurance={"authenticity_threshold": 0.5},
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
        sample=f.read(),
        applicant=applicant,
        content_type="audio/wav",
    )
```

## Read an account and its credentials

```python
from vericlient import VcspClient

client = VcspClient(apikey="your_api_key")

account = client.get_account(subject_id="user-1")
print(f"Created at {account.created_at}, {len(account.credentials)} credential(s)")

credentials = client.get_all_subject_credentials(subject_id="user-1").credentials
for credential in credentials:
    print(f"{credential.id}: {credential.sample.type}, valid until {credential.valid_until}")

one = client.get_credential(
    subject_id="user-1",
    credential_id=credentials[0].id,
)
print(one.claims, one.tags)
```

## Delete a credential or a whole account

Deleting an account removes every credential it holds. Both are permanent.

```python
from vericlient import VcspClient

client = VcspClient(apikey="your_api_key")

client.delete_credential(
    subject_id="user-1",
    credential_id="the-credential-id",
)
client.delete_account(subject_id="user-1")
```

## Handling failures

```python
from vericlient.vcsp.exceptions import AccountNotFoundError, AssuranceValidationError

try:
    client.enroll_subject(enrollment_input)
except AssuranceValidationError:
    print("The sample did not meet the assurance thresholds")

try:
    client.get_account(subject_id="does-not-exist")
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

client = VcspClient(apikey="your_api_key")

client.create_tags(tags=["role:employee", "region:eu"])

for tag in client.get_tags().items:
    print(f"{tag.name} (created {tag.created_at})")

client.delete_tag(name="region:eu")
```

Once a tag exists, pass it when enrolling:

```python
from vericlient.vcsp.models import Applicant

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

client = VcspClient(apikey="your_api_key")
configuration = next(c for c in client.get_credential_configurations().credential_configurations if "voice" in c)

group = client.create_group(
    name="support_agents",
    credential_configuration_urn=configuration,
)
print(f"{group.name} holds {group.size} credentials, expiring {group.expired_at}")

for g in client.get_groups().items:
    print(g.name)

members = client.get_group_members(name="support_agents")
print(f"{members.total} members")

client.delete_group(name="support_agents")
```

!!! warning "`expired_at` is a duration going in and a date coming out"

    `create_group`'s `expired_at` takes an **ISO 8601 duration** — a retention period such as
    `P1Y` or `P30D`, not a date. The service applies it and answers with the resulting
    timestamp in `CreateGroupOutput.expired_at`. Leave it out and credentials are retained
    for five years.

!!! note "Subscriptions cap the number of groups"

    Creating one past the limit raises `GroupsLimitExceededError`. The limit is part of the
    subscription, not something the client controls.

## Finding credentials across the whole system

`get_all_subject_credentials` is scoped to one account. `list_credentials` is not: it walks
everything, so filter and page rather than asking for the lot.

```python
from vericlient import VcspClient

client = VcspClient(apikey="your_api_key")

page = client.list_credentials(tags=["role:employee"], size=50)
print(f"{page.total} credentials over {page.pages} pages")
for credential in page.items:
    print(f"{credential.id} belongs to {credential.subject_id}")
```

Each item carries `subject_id`, which the per-account endpoints do not return — that is what
makes the listing useful for finding an account you only know a tag for.

## Retrieving the sample behind a credential

The service answers with the raw bytes it was enrolled with, not with JSON.

```python
sample = client.get_credential_sample(
    subject_id="user-1",
    credential_id=credential_id,
)
with open("recovered.wav", "wb") as f:
    f.write(sample.content)
print(sample.content_type)  # audio/wav
```

## Deleting credentials in bulk

```python
client.delete_credentials(
    group_name="support_agents",
    delete_empty_accounts=True,
)
```

!!! danger "Irreversible, and a group is the only filter"

    Credentials in the group are deleted and removed from every other group they belong to.
    With `delete_empty_accounts`, accounts left holding nothing go too. There is no way to
    scope this by tag or by account.

## Inspecting one credential configuration

`get_credential_configurations` lists the URNs; this returns the schema that an enrolment's
`claims` must satisfy for a given one.

```python
configuration = client.get_credential_configuration(
    urn="urn:vcsp:credential_configurations:voice_telephone:v1",
)
print(configuration.claims_schema)
```

## Enrolling in bulk

Batch enrolment is asynchronous: the service accepts the work and hands back a task to
follow. The client builds the archive it expects, so you pass applicants rather than
assembling a TAR yourself.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import Applicant, BatchApplicant

client = VcspClient(apikey="your_api_key")

batch = client.enroll_batch(
    applicants=[
        BatchApplicant(
            sample="/path/to/alice.wav",
            applicant=Applicant(
                subject_id="alice",
                credential_configuration_urn=configuration,
                assurance_method_urn=method,
                assurance={"authenticity_threshold": 0.5},
            ),
        ),
        BatchApplicant(sample="/path/to/bob.wav", applicant=bob),
    ],
)

task = client.wait_for_task(task_id=batch.task_id, timeout=300)
if not task.succeeded:
    raise RuntimeError(f"batch finished as {task.status}")

result = client.get_task_result(task_id=batch.task_id).result
print(result["summary"])  # {'total': 2, 'success': 2, 'error': 0}
for item in result["report"]:
    print(item["subject_id"], item["status"])
```

A batch can partly succeed: `summary` counts both outcomes and `report` carries one entry
per applicant, so check the report rather than only the task status.

`sample` takes a path or bytes, as everywhere else. `filename` sets the name inside the
archive if you need it to be something particular; otherwise it is derived.

## Following asynchronous work

Anything that answers `202` runs as a task.

```python
# Everything still running or recently finished
for task in client.get_tasks().items:
    print(f"{task.task_id}: {task.status} at {task.progress}%")

# One task, checked once
task = client.get_task(task_id=task_id)
if task.status == TaskStatus.FAILED:
    ...

# Or block until it finishes
task = client.wait_for_task(task_id=task_id, timeout=300, poll_interval=2)
print(task.is_finished, task.succeeded)

client.delete_task(task_id=task_id)
```

`wait_for_task` returns on failure as well as on success — check `succeeded` rather than
assuming. It raises `TimeoutError` if the task is still running when the timeout expires.

!!! note "`status` is a plain string"

    `TaskStatus` exists to compare against, but the field is typed as `str` so a state the
    service adds later does not break deserialisation.

!!! tip "Tasks expire on their own"

    The service drops a task and its result after thirty days. `delete_task` is there for
    callers that would rather not wait.

## Matching

Matching is what the stored credentials are for. Pass a `SubjectClaimant` to check a sample
against one subject, or a `GroupClaimant` to search a whole group.

```python
from vericlient import VcspClient
from vericlient.vcsp.models import GroupClaimant, SubjectClaimant

client = VcspClient(apikey="your_api_key")
method = "urn:vcsp:assurance_methods:matching:biometric_threshold:v1"

# 1:1 — is this the person they claim to be?
result = client.match(
    sample="/path/to/caller.wav",
    claimant=SubjectClaimant(
        subject_id="alice",
        credential_configuration_urn=configuration,
        assurance_method_urn=method,
        assurance={"biometric_threshold": 0.5},
    ),
)
print(result.results[0].match_status)  # HIT or MISS
print(result.results[0].biometrics_score)  # 0.0 to 1.0

# 1:N — who in this group is it?
result = client.match(
    sample="/path/to/caller.wav",
    claimant=GroupClaimant(
        group_name="support_agents",
        assurance_method_urn=method,
        assurance={"biometric_threshold": 0.5},
        limit=5,
        filter={"AND": [{"tag": "role:employee"}]},
    ),
)
print(f"{result.nhits} hits out of {len(result.results)} candidates")
```

`result.sample` carries what the service made of the recording — its type, the media type it
was read as, and quality figures such as `net_speech_duration`.

!!! note "A large 1:N runs asynchronously"

    The service may accept the work instead of answering. `match` then returns a
    `TaskCreatedOutput` rather than a `MatchingOutput`, to follow with `wait_for_task`.

## Putting credentials into a group

A credential does not join a group at enrolment: it is added afterwards, by subject or by
tag.

```python
from vericlient.vcsp.models import GroupAction, GroupMembershipSource

# By subject
client.modify_group(
    name="support_agents",
    action=GroupAction.POPULATE,
    from_=GroupMembershipSource(subjects=["alice", "bob"]),
)

# Or by tag, which scales better
client.modify_group(
    name="support_agents",
    action=GroupAction.POPULATE,
    from_=GroupMembershipSource(tags=["role:employee"]),
    credential_ttl="P30D",
)

# Taking them out again
client.modify_group(
    name="support_agents",
    action=GroupAction.REMOVE,
    from_=GroupMembershipSource(subjects=["bob"]),
)
```

The argument is `from_`, because `from` is a reserved word in Python; it is sent as `from`.
A small change answers with the group, a large population is accepted as a task.

## Changing a credential's tags

The tags must already exist — create them with `create_tags` first.

```python
from vericlient.vcsp.models import CredentialTagAction

credential = client.modify_credential_tags(
    subject_id="alice",
    credential_id=credential_id,
    action=CredentialTagAction.ADD,
    tags=["region:eu"],
)
print(credential.tags)
```

## Clustering a group

Clustering groups similar credentials together, to find duplicates or related enrolments. It
runs as a task.

```python
task = client.start_clustering(
    name="onboarding_faces",
    assurance_method_urn="urn:vcsp:assurance_methods:clustering:thresholds:v1",
    properties={"similarity_threshold": 0.5, "mode": "similarity_based"},
)
client.wait_for_task(task_id=task.task_id)
```

!!! warning "Face credentials only"

    A group of voice credentials is rejected with `ClusteringNotSupportedError`.

!!! note "The field is `properties`, not `assurance`"

    Every other endpoint calls the values an assurance method requires `assurance`.
    Clustering calls them `properties`.
