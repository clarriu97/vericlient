"""Example script to demonstrate how to use the Vcsp module.
"""
from vericlient import VcspClient
from vericlient.vcsp.models import (
    EnrollmentInput,
    AssuranceMethodInput,
    GetAccountInput,
    DeleteAccountInput,
    GetCredentialsInput,
    GetCredentialInput,
    DeleteCredentialInput,
    Applicant,
    CreateGroupInput,
    GetGroupInput,
    DeleteGroupInput,
    GetGroupsInput,
    GetGroupMembersInput,
    CreateTagsInput,
    DeleteTagInput,
)


client = VcspClient()

# check if the server is alive
print()
print(f"Alive: {client.alive()}")

# get all credential configurations
credential_configurations = client.get_credential_configurations()
print()
print(f"Credential configurations: {credential_configurations.credential_configurations}")

# get all assurance methods
print()
assurance_methods = client.get_assurance_methods()
print(f"Assurance methods: {assurance_methods.assurance_methods}")

# get an assurance method
all_assurance_methods = []
for assurance_method in assurance_methods.assurance_methods:
    assurance_method_data = client.get_assurance_method_info(
        data_model=AssuranceMethodInput(urn=assurance_method)
    )
    all_assurance_methods.append(assurance_method_data)

print()
print(f"Each assurance method individually: {all_assurance_methods}")

credential_configuration_urn = [
    credential_configuration for credential_configuration in credential_configurations.credential_configurations
    if "telephone" in credential_configuration
][0]
assurance_method_urn = [
    assurance_method for assurance_method in assurance_methods.assurance_methods
    if "enrollment:thresholds" in assurance_method
][0]

# enroll a subject specifying the subject id
enrollment_data = client.enroll_subject(
    data_model=EnrollmentInput(
        sample="tests/daspeak/resources/audio.wav",
        applicant=Applicant(
            subject_id="user1",
            credential_configuration_urn=credential_configuration_urn,
            assurance_method_urn=assurance_method_urn,
            assurance={"authenticity_threshold": 0.5},
        )
    )
)
print()
print(f"User enrolled: {enrollment_data}")

# enroll a subject without specifying the subject id
enrollment_data = client.enroll_subject(
    data_model=EnrollmentInput(
        sample="tests/daspeak/resources/audio.wav",
        applicant=Applicant(
            credential_configuration_urn=credential_configuration_urn,
            assurance_method_urn=assurance_method_urn,
            assurance={"authenticity_threshold": 0.5},
        )
    )
)
print()
print(f"User enrolled: {enrollment_data}")

# get the account data
account_data = client.get_account(
    data_model=GetAccountInput(
        subject_id="user1"
    )
)
print()
print(f"Account data: {account_data}")

# get all credentials from a subject
credentials = client.get_all_subject_credentials(
    data_model=GetCredentialsInput(
        subject_id="user1"
    )
)
print()
print(f"Credentials for user1: {credentials.credentials}")

# get a credential from a subject
credential = client.get_credential(
    data_model=GetCredentialInput(
        subject_id="user1",
        credential_id=credentials.credentials[0].id
    )
)
print()
print(f"First credential for user1: {credential}")

# delete a credential
client.delete_credential(
    data_model=DeleteCredentialInput(
        subject_id="user1",
        credential_id=credentials.credentials[0].id
    )
)
print()
print(f"Credential deleted for user1: {credentials.credentials[0].id}")

# delete the account
client.delete_account(
    data_model=DeleteAccountInput(
        subject_id="user1"
    )
)
client.delete_account(
    data_model=DeleteAccountInput(
        subject_id=enrollment_data.subject_id
    )
)
print()
print(f"Accounts deleted: {enrollment_data.subject_id} and user1")

# create a group
group = client.create_group(
    data_model=CreateGroupInput(
        credential_configuration_urn=credential_configuration_urn,
        name="test_group",
        description="Test group",
        expired_at="P1D",  # 1 day from now
    )
)
print()
print(f"Group created: {group}")

# get the group
group = client.get_group(
    data_model=GetGroupInput(
        name="test_group"
    )
)
print()
print(f"Group retrieved: {group}")

# get the group members
group_members = client.get_group_members(
    data_model=GetGroupMembersInput(
        name="test_group"
    )
)
print()
print(f"Group members: {group_members.items}")
print(f"Total group members: {group_members.total}")
print(f"Page: {group_members.page}")
print(f"Size: {group_members.size}")
print(f"Pages: {group_members.pages}")

# delete the group
client.delete_group(
    data_model=DeleteGroupInput(
        name="test_group"
    )
)
print()
print(f"Group deleted: {group}")

# get all groups
groups = client.get_groups(
    data_model=GetGroupsInput(
        size=100,
        page=1
    )
)
print()
print(f"Groups: {groups}")
print(f"Total groups: {groups.total}")
print(f"Page: {groups.page}")
print(f"Pages: {groups.pages}")
print(f"Size: {groups.size}")

# create tags
tags = client.create_tags(
    data_model=CreateTagsInput(
        tags=["test:tag1", "test:tag2"]
    )
)
print()
print(f"Tags created: {tags}")

# get all tags
all_tags = client.get_tags()
print()
print(f"All tags: {all_tags}")

# delete a tag
client.delete_tag(
    data_model=DeleteTagInput(
        name="test:tag1"
    )
)
client.delete_tag(
    data_model=DeleteTagInput(
        name="test:tag2"
    )
)
print()
print(f"Tags deleted: {tags}")
