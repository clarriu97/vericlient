"""Example script showing how to use the VCSP client.

Runnable as it stands against a sandbox: it creates an account, a group and two tags, and
removes all of them before it ends. It needs `VERICLIENT_APIKEY` in the environment.

The names are prefixed so that anything left behind by a run that died halfway is obvious.
"""

import os
import uuid

from vericlient import VcspClient
from vericlient.vcsp.models import Applicant, SubjectClaimant

SAMPLE = os.environ.get("SAMPLE", "tests/daspeak/resources/audio.wav")
SUBJECT = f"vericlient-example-{uuid.uuid4().hex[:8]}"
GROUP = f"vericlient_example_{uuid.uuid4().hex[:8]}"
TAGS = ["example:one", "example:two"]

client = VcspClient()

print(f"Alive: {client.alive()}")

# Which configurations and methods this subscription offers. Both differ between
# subscriptions, so they are read rather than hardcoded.
configurations = client.get_credential_configurations().credential_configurations
methods = client.get_assurance_methods().assurance_methods
print(f"Credential configurations: {configurations}")
print(f"Assurance methods: {methods}")

configuration = next(c for c in configurations if "telephone" in c)
method = next(m for m in methods if "enrollment:thresholds" in m)
matching_method = next(m for m in methods if "matching:biometric_threshold" in m)
print(f"Assurance method in detail: {client.get_assurance_method_info(urn=method)}")

# Enrolling with a subject id of your own.
enrollment = client.enroll_subject(
    sample=SAMPLE,
    applicant=Applicant(
        subject_id=SUBJECT,
        credential_configuration_urn=configuration,
        assurance_method_urn=method,
        assurance={"authenticity_threshold": 0.5},
    ),
)
print(f"Enrolled {enrollment.subject_id} with credential {enrollment.credential_id}")

# Leaving it out, so VCSP generates one.
generated = client.enroll_subject(
    sample=SAMPLE,
    applicant=Applicant(
        credential_configuration_urn=configuration,
        assurance_method_urn=method,
        assurance={"authenticity_threshold": 0.5},
    ),
)
print(f"Enrolled with a generated subject id: {generated.subject_id}")

print(f"Account: {client.get_account(subject_id=SUBJECT)}")

credentials = client.get_all_subject_credentials(subject_id=SUBJECT).credentials
print(f"Credentials held by {SUBJECT}: {credentials}")
print(f"One of them in detail: {client.get_credential(subject_id=SUBJECT, credential_id=credentials[0].id)}")

# Matching is what the credentials are for: a fresh sample against one subject.
matching = client.match(
    sample=SAMPLE,
    claimant=SubjectClaimant(
        subject_id=SUBJECT,
        credential_configuration_urn=configuration,
        assurance_method_urn=matching_method,
        assurance={"biometric_threshold": 0.5},
    ),
)
print(f"Matched against {SUBJECT}: {matching}")

# Deleting a credential leaves the account; deleting the account takes everything.
client.delete_credential(subject_id=SUBJECT, credential_id=credentials[0].id)
print(f"Credential deleted: {credentials[0].id}")

client.delete_account(subject_id=SUBJECT)
client.delete_account(subject_id=generated.subject_id)
print(f"Accounts deleted: {SUBJECT} and {generated.subject_id}")

# Groups hold credentials for 1:N matching.
group = client.create_group(
    credential_configuration_urn=configuration,
    name=GROUP,
    description="Created by the example script",
    expired_at="P1D",  # an ISO 8601 duration: how long it is kept, not a date
)
print(f"Group created: {group}")
print(f"Group read back: {client.get_group(name=GROUP)}")
print(f"Group members: {client.get_group_members(name=GROUP).items}")

client.delete_group(name=GROUP)
print(f"Group deleted: {GROUP}")
print(f"Groups now: {client.get_groups().total}")

# A credential can only carry tags the subscription already knows about.
print(f"Tags created: {client.create_tags(tags=TAGS)}")
print(f"All tags: {client.get_tags().total}")
for tag in TAGS:
    client.delete_tag(name=tag)
print(f"Tags deleted: {TAGS}")
