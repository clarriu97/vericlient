# Changelog

## Unreleased

## 0.2.0

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

- **das-Peak is now fully covered**: `get_model_metadata`, `get_model_calibrations` and
  `get_model_metadata_from_credential` complete the eleven endpoints in the specification.
  Three of them had entries in `DaspeakEndpoints` but no method, while the README claimed
  full support.
- `ModelNotAvailableError`, raised when a model hash does not exist.
- `EnrollmentInput.content_type`, for when the sniffed media type will not do.
- `utils.guess_content_type`.

### Internal

- Every dependency refreshed; no known vulnerabilities in the resolved set.
- CI rebuilt: matrix over 3.11–3.14, `ruff format --check`, and a `pip-audit` stage that
  reports into the run summary.
- Weekly automated dependency updates, verified before they reach a pull request.
