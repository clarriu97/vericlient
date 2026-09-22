# Changelog

Notable changes to `vericlient`, newest first. Dates are the day the version was released.
The project follows [semantic versioning](https://semver.org/).

## Unreleased

### Added

- **A das-Face client**, covering `alive`, `get_models`, `generate_credential` and
  `get_model_metadata_from_credential` — 4 of the 11 endpoints in the v3.35 specification.
  das-Face takes JSON with base64 images rather than multipart parts, uses camelCase fields
  and is served under `/v2`; none of that reaches the caller.
- `utils.encode_base64`.
- The real-infrastructure coverage guard now covers every client, not just VCSP.

## [0.3.0] — 2026-09-22

VCSP goes from a third of its API to all of it, and the client stops leaking HTTP details
into its return values.

### Breaking

- **Responses no longer carry `status_code`.** An HTTP status code is a transport detail,
  and surfacing it on a client's return value invites callers to branch on it instead of
  relying on the exceptions the client already raises. `DaspeakResponse` keeps `version`;
  `VcspResponse` now carries no fields and exists only as a shared type.

### Added

- Every public `VcspClient` method is exercised against real infrastructure, guarded by a
  test that fails if one is added without it.
- **VCSP is now fully covered**: `match` for 1:1 and 1:N biometric matching, `modify_group`
  to populate or empty a group, `modify_credential_tags`, and `start_clustering`. All 31
  endpoints in the specification are reachable.
- **VCSP batch enrolment and task management**: `enroll_batch`, `get_tasks`, `get_task`,
  `delete_task`, `get_task_result` and `wait_for_task`. Coverage reaches 27 of 31 endpoints.
  The client builds the TAR archive batch enrolment expects, whose layout is documented
  nowhere and was worked out from the service's error messages.
- **VCSP credential listing and configuration lookup**: `list_credentials`,
  `delete_credentials`, `get_credential_sample` and `get_credential_configuration`. Coverage
  reaches 22 of the 31 endpoints.
- **VCSP groups and tags**: `create_group`, `get_groups`, `get_group`, `delete_group`,
  `get_group_members`, `create_tags`, `get_tags` and `delete_tag`. Coverage goes from 10 to
  18 of the 31 endpoints in the specification.
- Exceptions for the new failure modes: `GroupNotFoundError`, `GroupAlreadyExistsError`,
  `GroupsLimitExceededError`, `TagAlreadyExistsError`, `TagsLimitExceededError`,
  `TagListEmptyError` and `EnrollmentsLimitExceededError`.
- The VCSP suite now creates and destroys real resources against a sandbox, with a session
  sweeper that recovers from a run that died before its teardown, and a `--keep-resources`
  flag for debugging.

## [0.2.0] — 2026-09-21

First release after a long gap. It carries breaking changes, all of them correcting
behaviour that was either wrong or impossible to use.

### Breaking

- **Configuration precedence is inverted.** A constructor argument now wins over the
  matching `VERICLIENT_` environment variable. Before, the environment silently won, so
  `DaspeakClient(apikey="x")` was ignored whenever `VERICLIENT_APIKEY` was set and two
  clients could not use two different keys in the same process.
- **`dynaconf` is gone**, replaced by `pydantic-settings`. `VERICLIENT_TIMEOUT` is now
  validated as an integer at client creation instead of failing later at request time.
- **das-Peak identification models renamed** to match the API:
  `CompareAudio2CredentialsInput.audio_reference` → `audio_to_evaluate`,
  `CompareCredential2CredentialsInput.credential_reference` → `credential_to_evaluate`,
  and on the output, `authenticity_reference`, `input_audio_duration_reference` and
  `net_speech_duration_reference` → their `_to_evaluate` counterparts. Safe, because both
  endpoints were sending the wrong field name and had never returned a result.
- **`AssuranceMethodOutput.schema` and `AssuranceMethodSchema.schema` are now
  `json_schema`.** The old name shadowed `BaseModel.schema`. JSON payloads are unchanged;
  `$schema` and `schema` remain as aliases.
- **`Client.__init__` takes an `APIs` member** instead of a string, and
  `VcspClient(api=...)` is gone.
- **Python 3.11 is the minimum.** The package is tested on 3.11, 3.12, 3.13 and 3.14.

### Fixed

- das-Peak `identification/wav2credentials` and `identification/credential2credentials`
  sent the wrong form field names and always answered 400.
- `Client._delete` returned `None` despite being annotated `-> requests.Response`.
- A non-JSON error body, such as a gateway's HTML 502 page, raised a raw `JSONDecodeError`
  instead of a `ServerError`.
- `VcspClient` could not accept a sample as bytes: it passed the bytes to
  `mimetypes.guess_type()` and raised `TypeError`. Media types are now sniffed from the
  content, and `EnrollmentInput` takes an optional `content_type`.
- The getting-started example in the documentation imported a `DasfaceClient` that does not
  exist.

### Added

- **The VCSP client reaches PyPI for the first time.** It was written between 0.1.6 and this
  release but never published, so every 0.1.x on PyPI carries das-Peak only.
- **das-Peak is now fully covered**: `get_model_metadata`, `get_model_calibrations` and
  `get_model_metadata_from_credential` complete the eleven endpoints in the specification.
  Three of them had entries in `DaspeakEndpoints` but no method, while the README claimed
  full support.
- `ModelNotAvailableError`, raised when a model hash does not exist.
- `EnrollmentInput.content_type`, for when the sniffed media type will not do.
- `utils.guess_content_type`.

### Documentation

- Documentation moved to **https://vericlient.larri.dev**, and the project URLs, README and
  badges follow it.
- The changelog is no longer duplicated: the documentation includes this file directly.
- A `py.typed` marker ships with the package, so type checkers use the annotations that were
  already there.

- A real quickstart on the home page, which previously held a `pip install` line and a link.
- **Supported endpoints** page, with per-API coverage checked against the OpenAPI
  specifications rather than claimed from memory.
- **Error handling** page describing the exception tree, which until now was only dumped by
  mkdocstrings with no explanation.
- The VCSP usage page grew from a single `alive()` example to cover everything implemented.
- Light and dark themes, copy buttons on code blocks, and a navigation that separates usage
  from API reference.
- `mkdocs build --strict`, so a broken internal link fails CI.
- Removed a reference to a `javascripts/extra.js` that is not in the repository and was
  404ing on every page.

### Internal

- Every dependency refreshed; no known vulnerabilities in the resolved set.
- CI rebuilt: matrix over 3.11–3.14, `ruff format --check`, and a `pip-audit` stage that
  reports into the run summary.
- Weekly automated dependency updates, verified before they reach a pull request.

## [0.1.6] — 2024-09-12

## [0.1.5] — 2024-09-12

## [0.1.4] — 2024-09-12

## [0.1.3] — 2024-09-12

## [0.1.2] — 2024-09-12

## [0.1.1] — 2024-09-12

Six releases in one afternoon, all of them the same library. Each one changed only
`.github/workflows/ci.yml` and the version number while the automated release pipeline was
being worked out: artifact naming, the release job, and the PyPI upload step. Nothing in
`src/` differs between 0.1.1 and 0.1.6.

## [0.1.0] — 2024-09-12

First release, never published to PyPI. It shipped the das-Peak client and the pieces
everything else is built on:

- `Client`, the shared request, error and target handling
- `DaspeakClient` with the alive, models, credential generation, similarity and
  identification endpoints
- Configuration through `VERICLIENT_` environment variables
- The `Environments` and `Locations` enums for cloud targets, and a `url` argument for
  self-hosted deployments

[0.3.0]: https://github.com/clarriu97/vericlient/releases/tag/v0.3.0
[0.2.0]: https://github.com/clarriu97/vericlient/releases/tag/v0.2.0
[0.1.6]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.6
[0.1.5]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.5
[0.1.4]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.4
[0.1.3]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.3
[0.1.2]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.2
[0.1.1]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.1
[0.1.0]: https://github.com/clarriu97/vericlient/releases/tag/v0.1.0
