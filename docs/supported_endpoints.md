# Supported endpoints

What the client covers today, checked endpoint by endpoint against the official OpenAPI
specifications rather than against memory.

| API | Specification | Covered |
|---|---|---|
| das-Peak | [v2.33](https://docs.veridas.com/das-peak/cloud/v2.33/api/definition/) | **11 / 11** |
| VCSP | [v1.17](https://docs.veridas.com/vcsp_echo/cloud/v1.17/api/definition/) | **27 / 31** |
| das-Face | [v2](https://docs.veridas.com/das-face/cloud/v3.26/api/definition/) | 0 / 14 |

---

## das-Peak

Fully covered.

| Endpoint | Client |
|---|---|
| `GET /v1/alive` | `alive()` |
| `GET /v1/models` | `get_models()` |
| `POST /v1/models/metadata` | `get_model_metadata()` |
| `POST /v1/models/calibration` | `get_model_calibrations()` |
| `POST /v1/models/metadata/from-credential` | `get_model_metadata_from_credential()` |
| `POST /v1/models/{hash}/credential/wav` | `generate_credential()` |
| `POST /v1/similarity/credential2credential` | `compare(CompareCredential2CredentialInput)` |
| `POST /v1/similarity/credential2wav` | `compare(CompareCredential2AudioInput)` |
| `POST /v1/similarity/wav2wav` | `compare(CompareAudio2AudioInput)` |
| `POST /v1/identification/wav2credentials` | `compare(CompareAudio2CredentialsInput)` |
| `POST /v1/identification/credential2credentials` | `compare(CompareCredential2CredentialsInput)` |

## VCSP

Work in progress, tracked in [issue #3](https://github.com/clarriu97/vericlient/issues/3).

| Endpoint | Client |
|---|---|
| `GET /v1/alive` | `alive()` |
| `POST /v1/enrollments` | `enroll_subject()` |
| `POST /v1/enrollments/batch` | `enroll_batch()` |
| `GET /v1/accounts/{subject_id}` | `get_account()` |
| `DELETE /v1/accounts/{subject_id}` | `delete_account()` |
| `GET /v1/accounts/{subject_id}/credentials` | `get_all_subject_credentials()` |
| `GET /v1/accounts/{subject_id}/credentials/{credential_id}` | `get_credential()` |
| `DELETE /v1/accounts/{subject_id}/credentials/{credential_id}` | `delete_credential()` |
| `GET /v1/accounts/{subject_id}/credentials/{credential_id}/sample` | `get_credential_sample()` |
| `PATCH /v1/accounts/{subject_id}/credentials/{credential_id}/tags` | — |
| `GET /v1/credentials` | `list_credentials()` |
| `DELETE /v1/credentials` | `delete_credentials()` |
| `POST /v1/groups` | `create_group()` |
| `GET /v1/groups` | `get_groups()` |
| `GET /v1/groups/{group_name}` | `get_group()` |
| `PATCH /v1/groups/{group_name}` | — |
| `DELETE /v1/groups/{group_name}` | `delete_group()` |
| `GET /v1/groups/{group_name}/credentials` | `get_group_members()` |
| `POST /v1/groups/{group_name}/clustering` | — |
| `POST /v1/matchings` | — |
| `GET /v1/credential_configurations` | `get_credential_configurations()` |
| `GET /v1/credential_configurations/{urn}` | `get_credential_configuration()` |
| `GET /v1/assurance_methods` | `get_assurance_methods()` |
| `GET /v1/assurance_methods/{urn}` | `get_assurance_method_info()` |
| `POST /v1/tags` | `create_tags()` |
| `GET /v1/tags` | `get_tags()` |
| `DELETE /v1/tags/{tag_name}` | `delete_tag()` |
| `GET /v1/tasks` | `get_tasks()` |
| `GET /v1/tasks/{task_id}` | `get_task()`, `wait_for_task()` |
| `DELETE /v1/tasks/{task_id}` | `delete_task()` |
| `GET /v1/tasks/{task_id}/result` | `get_task_result()` |

## das-Face

Not started, tracked in [issue #4](https://github.com/clarriu97/vericlient/issues/4). Note
that das-Face is served under `/v2`, unlike the other two.

## Other Veridas APIs

vali-Das ([#8](https://github.com/clarriu97/vericlient/issues/8)) and eSign
([#9](https://github.com/clarriu97/vericlient/issues/9)) have exploratory branches but no
supported client yet.
