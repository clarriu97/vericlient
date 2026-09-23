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

The model is part of the credential, so you have to say which one to use. Take it from
`get_models()`:

```python
from vericlient import DasfaceClient

client = DasfaceClient(apikey="your_api_key")

model = max(
    (m for m in client.get_models().models if m.mode == "default-mode"),
    key=lambda m: m.tag,
)

credential = client.generate_credential(
    image="/path/to/face.jpg",
    hash=model.hash,
    mode=model.mode,
)
print(credential.credential)
print(f"generated with {credential.model.hash} in {credential.model.mode}")
```

A hash on its own is not enough — the model is identified by hash *and* mode together, and
passing one without the other is rejected before any request is made.

!!! warning "There is no endpoint that picks a model for you"

    das-Face used to have one, `POST /v2/credential/photo`. The v3.26 specification marks it
    deprecated in favour of `/v2/models/{hash}/{mode}/credential/photo`, v3.35 drops it, and
    `work`/`eu` does not route it, so the client offers no model-less form outside INE Mexico.
    Store the hash and mode alongside every credential you keep: a credential only compares
    against another made with the same model.

The photo can be a path or a `bytes` object:

```python
with open("/path/to/face.jpg", "rb") as f:
    credential = client.generate_credential(
        image=f.read(),
        hash=model.hash,
        mode=model.mode,
    )
```

## Find out which model generated a credential

Useful to check whether a credential you stored some time ago still matches a model the
service offers today.

```python
metadata = client.get_model_metadata_from_credential(
    credential=stored_credential,
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
    client.generate_credential(
        image=photo,
        hash=model.hash,
        mode=model.mode,
    )
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

client = DasfaceClient(apikey="your_api_key")

# against another photo
result = client.verify_photo(
    anchor_image="/path/to/enrolled.jpg",
    target_image="/path/to/live.jpg",
)

# against a video, which is what a liveness capture gives you
result = client.verify_video(
    anchor_image="/path/to/enrolled.jpg",
    target_video="/path/to/capture.mp4",
)

# against a stored credential, which is the everyday case
result = client.verify_credential(
    anchor_image="/path/to/live.jpg",
    target_credential=stored_credential,
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
client.verify_photo(anchor_image=enrolled, target_image=live, mode="document-mode")
```

!!! warning "`rotatePhotos` does not exist"

    The v3.26 specification documents a `rotatePhotos` field on this endpoint. The service
    rejects it — `Unknown field name 'rotatePhotos'` — and v3.35 has dropped it. This client
    does not offer it. See [#30](https://github.com/clarriu97/vericlient/issues/30).

## Checking authenticity

Verification answers "is this the same person?". Authenticity answers a different question:
"is this a real capture, or a photo of a screen?". A presentation attack passes verification
perfectly — it is the same face, after all — so the two checks go together.

```python
# A selfie
result = client.check_photo_authenticity(image="/path/to/selfie.jpg")
print(result.confidence)

# A video, which answers both questions at once
result = client.check_video_authenticity(
    anchor_image="/path/to/enrolled.jpg",
    target_video="/path/to/capture.mp4",
)
print(result.authenticity)  # is the recording genuine
print(result.similarity)  # is it the right person
```

The two figures from a video are independent, and that is the point: a genuine recording of
somebody else scores high on `authenticity` and low on `similarity`.

!!! warning "The face has to be big enough"

    Authenticity is the one place where image size alone decides. A face that occupies too
    little of the frame is **refused** with `FaceTooSmallForIasError`, not scored low — which
    means very different things to a caller. Against the real service a 450x600 photo passes
    and a 50x63 one is rejected.

## Liveness challenges

The authenticity endpoints ask whether a recording is genuine. A challenge asks something
harder to fake: whether it was recorded *just now*, in response to instructions the recorder
could not have known in advance.

It is a two-step flow. Generate a challenge, show its actions to the person, record them, and
send the recording back with the same token.

```python
from vericlient import DasfaceClient

client = DasfaceClient(apikey="your_api_key")

challenge = client.generate_sequential_challenge(length=3)

for action in challenge.actions:
    print(f"{action.name}: {action.action_class} {action.parameters}")
# action-0: move-head-and-back {'direction': 'right'}
# action-1: move-head-and-back {'direction': 'top'}
# action-2: move-head-and-back {'direction': 'bottom'}
```

`length` is how many actions to ask for, from 1 to 6 — the service calls 2 standard security
and 6 high security — and `expiration` how long the challenge stays valid, from 300 to 1800
seconds. Both are optional, and the service applies its own defaults when they are left out.

The service answers with a signed token rather than JSON. `challenge.token` is it, exactly as
it arrived: hand it to the capture SDK and send it back unchanged. The other fields are read
out of it for convenience.

Once the recording is in, along with the SDK's WebVTT annotations of it:

```python
result = client.analyse_challenge_response(
    token=challenge.token,
    annotations="/path/to/annotations.vtt",
    anchor_image="/path/to/face.jpg",
    target_video="/path/to/recording.mp4",
)

if result.confidence is None:
    for error in result.errors:
        print(f"could not analyse it: {error.code} — {error.message}")
elif result.confidence > 0.9:
    print("genuine, live, and the right person")
```

One figure answers all of it at once: whether the recording is genuine, whether it performs
the challenge that was issued, and whether the face in it is the one in the anchor photo.

!!! warning "This endpoint reports failures inside a successful response"

    It is the only one here that does. A face too small to analyse raises
    `FaceTooSmallForIasError` everywhere else; on this endpoint the same condition comes back
    as `200` with `confidence` set to `None` and the reason in `errors`. Check for `None`
    rather than assuming a number.

A challenge that has run out of time raises `ExpiredOrInvalidChallengeError`, and so does one
whose token has been altered — the signature is the point of it.

!!! note "Where these endpoints are documented"

    In the **v3.26** specification, not the current v3.35, which dropped them while the
    service kept answering. They are covered here because there is no liveness flow without
    them, and flagged in
    [#30](https://github.com/clarriu97/vericlient/issues/30) so Veridas can say which it is.

## The INE Mexico variant

das-Face exposes a separate credential endpoint for INE Mexico. It takes the same photo and
answers with the same shape, but lives under its own path and needs a specific agreement with
Veridas, so it is not enabled on every subscription.

```python
credential = client.generate_credential(
    image="/path/to/face.jpg",
    hash=model.hash,
    mode=model.mode,
    inemex=True,
)
```

It is the one credential endpoint with a default-model form, so here `hash` and `mode` may be
left out:

```python
credential = client.generate_credential(
    image="/path/to/face.jpg",
    inemex=True,
)
```

!!! warning "Its default model is not the newest one"

    `POST /v2/models/inemex/default-mode/credential/photo` reads like a generic default and is
    not: against `work`/`eu` it resolves to an older model than `get_models()` leads with. Use
    it only if you mean the INE Mexico model, and read `credential.model` to see which one you
    got.
