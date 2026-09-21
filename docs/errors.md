# Error handling

Every exception the client raises inherits from `VeriClientError`, so a single `except`
catches anything the library can throw:

```python
from vericlient.exceptions import VeriClientError

try:
    client.generate_credential(model_input)
except VeriClientError as error:
    print(f"The call did not go through: {error}")
```

Most of the time you want something narrower. The tree is shallow on purpose.

## Shared

| Exception | Raised when |
|---|---|
| `VeriClientError` | Base class. Never raised directly. |
| `AuthorizationError` | The API key is missing or rejected. |
| `ServerError` | The service failed, or answered something the client cannot interpret — including an error body that is not JSON. |
| `UnsupportedMediaTypeError` | The service does not accept the media type that was sent. |
| `InvalidCredentialError` | A credential is malformed or not accepted. |

## das-Peak

All of these inherit from `DaspeakError`. The ones about the audio itself inherit from
`AudioInputError`, so you can catch every "this recording will not do" case at once:

```python
from vericlient.daspeak.exceptions import AudioInputError
```

| Exception | Raised when |
|---|---|
| `TooManyAudioChannelsError` | The audio has more than two channels. |
| `UnsupportedSampleRateError` | The sample rate is neither 8 kHz nor 16 kHz. |
| `AudioDurationTooLongError` | The recording is longer than 30 seconds. |
| `UnsupportedAudioCodecError` | The codec is not `PCM_16`, `ULAW` or `ALAW`. |
| `SignalNoiseRatioError` | The recording is too noisy. |
| `NetSpeechDurationIsNotEnoughError` | Less than 3 seconds of actual speech. Carries the duration that was detected. |
| `InsufficientQualityError` | The quality is too low, or more than one speaker is present. |
| `InvalidSpecifiedChannelError` | The requested channel is neither 1 nor 2. |
| `CalibrationNotAvailableError` | The model does not support that calibration. Use `get_model_calibrations()` to see which ones it does. |
| `ModelNotAvailableError` | No model exists with that hash. |

!!! tip "Net speech, not duration"

    `NetSpeechDurationIsNotEnoughError` is about *speech*, not file length. A 10 second
    recording with 2 seconds of talking in it will still be rejected. The exception message
    carries the duration the service actually detected.

## VCSP

All of these inherit from `VcspError`.

| Exception | Raised when |
|---|---|
| `EmptyFileError` | The sample carries no content. |
| `InvalidClaimsError` | The claims do not satisfy the credential configuration. |
| `InvalidAssuranceError` | The assurance does not satisfy the assurance method. |
| `InvalidTagsError` | One of the tags is not valid. |
| `InvalidCredentialConfigurationUrnError` | No credential configuration with that URN. |
| `InvalidAssuranceMethodUrnError` | No assurance method with that URN. |
| `CredentialConfigurationUrnAlreadyAssignedError` | The subject already holds a credential with that configuration. |
| `InvalidAudioFormatError` | The audio format is not accepted. |
| `InvalidSnrError` | The audio is too noisy. |
| `VoiceDurationIsNotEnoughError` | Not enough speech in the sample. |
| `InsufficientQualityError` | The sample quality is too low. |
| `FaceNotFoundError` | No face in the image. |
| `MoreThanOneFaceError` | More than one face in the image. |
| `FaceTooSmallError` | The face is too small to be usable. |
| `FaceAlignmentError` | The face is not aligned well enough. |
| `AssuranceValidationError` | The sample did not meet the assurance thresholds. |
| `AssuranceMethodNotFoundError` | No assurance method with that URN. |
| `AccountNotFoundError` | No account with that subject id. |
| `CredentialNotFoundError` | No credential with that id. |
| `RequestValidationError` | The request is malformed. |

## A note on media types

VCSP answers **500** when the media type declared in the request does not match the content
it receives, so a client-side mistake can look like a server fault. The client guards
against this by declaring the media type per multipart part, inferring it from the file
extension for a path and from the magic bytes for a bytes object. Where the guess would be
wrong, set it explicitly:

```python
from vericlient.vcsp.models import EnrollmentInput

EnrollmentInput(sample=raw_bytes, applicant=applicant, content_type="audio/wav")
```
