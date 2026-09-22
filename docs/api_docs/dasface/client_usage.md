# das-Face Client usage

Examples for the [das-Face](https://docs.veridas.com/das-face/cloud/v3.35/) client, the face
counterpart of das-Peak.

See [Supported endpoints](../../supported_endpoints.md) for what is covered so far.

!!! note "das-Face is spoken to differently"

    Under the hood it takes JSON with base64 images rather than multipart file parts, its
    fields are camelCase, and it is served under `/v2` where the others are on `/v1`. None of
    that reaches you: images go in as a path or as bytes, and attributes keep their Python
    names.

## Check if the API is alive

```python
from vericlient import DasfaceClient

client = DasfaceClient(apikey="your_api_key")

print(f"Alive: {client.alive()}")
```

## List the biometrics models

The service returns one entry per hash **and mode**, so the same hash appears several times —
once for `default-mode`, once for `document-mode`, and so on.

```python
from vericlient import DasfaceClient

client = DasfaceClient(apikey="your_api_key")

for model in client.get_models().models:
    print(f"{model.hash[:12]}… {model.mode} (tag {model.tag}, {model.length} dimensions)")
```

## Generate a credential from a photo

A credential is the biometric representation of a face: it is what you store, and what you
compare against later.

```python
from vericlient import DasfaceClient
from vericlient.dasface.models import GenerateCredentialInput

client = DasfaceClient(apikey="your_api_key")

credential = client.generate_credential(GenerateCredentialInput(image="/path/to/face.jpg"))
print(credential.credential)
print(f"generated with {credential.model.hash} in {credential.model.mode}")
```

With no `hash` and `mode` the service picks its current default model, which is what you want
unless you are pinning one deliberately:

```python
model = next(m for m in client.get_models().models if m.mode == "document-mode")

credential = client.generate_credential(
    GenerateCredentialInput(image="/path/to/face.jpg", hash=model.hash, mode=model.mode),
)
```

A hash on its own is not enough — the model is identified by hash *and* mode together, and
passing one without the other is rejected before any request is made.

The photo can be a path or a `bytes` object:

```python
with open("/path/to/face.jpg", "rb") as f:
    credential = client.generate_credential(GenerateCredentialInput(image=f.read()))
```

## Find out which model generated a credential

Useful to check whether a credential you stored some time ago still matches a model the
service offers today.

```python
from vericlient.dasface.models import GetModelMetadataFromCredentialInput

metadata = client.get_model_metadata_from_credential(
    GetModelMetadataFromCredentialInput(credential=stored_credential),
).metadata
print(f"{metadata.hash} · {metadata.mode} · tag {metadata.tag}")
```

If the model has since been withdrawn, this raises `ObsoleteCredentialModelError`, which
means the credential has to be regenerated from the original photo.

## Handling failures

```python
from vericlient.dasface.exceptions import (
    DasfaceApiError,
    FaceNotFoundError,
    FaceTooSmallForIasError,
    MoreThanOneFaceError,
)
from vericlient.exceptions import InvalidCredentialError

try:
    client.generate_credential(GenerateCredentialInput(image=photo))
except FaceNotFoundError:
    print("no face in that photo")
except MoreThanOneFaceError:
    print("crop it to one face")
except FaceTooSmallForIasError:
    print("the face needs to fill more of the frame")
except DasfaceApiError as error:
    print(f"the service reported {error.code}")
```

!!! tip "Unrecognised codes are not swallowed"

    das-Face's error codes are documented in the v3.35 specification but the set is
    open-ended, and two codes it returns are not in it at all. Any code this client does not
    map surfaces as `DasfaceApiError` carrying the service's own code and message, rather
    than disappearing into a generic server error.

The full list is in [Error handling](../../errors.md).

## Verifying a face

Three ways to ask the same question — is this the same person?

```python
from vericlient import DasfaceClient
from vericlient.dasface.models import (
    VerifyCredentialInput,
    VerifyPhotoInput,
    VerifyVideoInput,
)

client = DasfaceClient(apikey="your_api_key")

# against another photo
result = client.verify_photo(
    VerifyPhotoInput(anchor_image="/path/to/enrolled.jpg", target_image="/path/to/live.jpg"),
)

# against a video, which is what a liveness capture gives you
result = client.verify_video(
    VerifyVideoInput(anchor_image="/path/to/enrolled.jpg", target_video="/path/to/capture.mp4"),
)

# against a stored credential, which is the everyday case
result = client.verify_credential(
    VerifyCredentialInput(anchor_image="/path/to/live.jpg", target_credential=stored_credential),
)

print(result.confidence)
```

`verify_credential` is the one most integrations want: the credential is generated once at
enrolment, and every later check compares a fresh photo against it without keeping the
original around.

Against a real service, the same face scores about **0.99995** and two different faces about
**0.027**, so the two cases are not close together.

`verify_photo` also takes a `mode`, to pin the model mode rather than let the service choose:

```python
VerifyPhotoInput(anchor_image=enrolled, target_image=live, mode="document-mode")
```

!!! warning "`rotatePhotos` does not exist"

    The v3.26 specification documents a `rotatePhotos` field on this endpoint. The service
    rejects it — `Unknown field name 'rotatePhotos'` — and v3.35 has dropped it. This client
    does not offer it. See [#30](https://github.com/clarriu97/vericlient/issues/30).
