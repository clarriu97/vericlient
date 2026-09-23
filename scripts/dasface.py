"""Example script showing how to use the das-Face client.

Runnable as it stands: it defaults to the repository's own test media, so
`pdm run python scripts/dasface.py` works in a checkout. It needs `VERICLIENT_APIKEY` in the
environment, and creates nothing that has to be cleaned up.

The INE Mexico endpoints are not exercised here: they need a specific agreement with Veridas
and are not enabled on every subscription.
"""

import os

from vericlient import DasfaceClient

PHOTO = os.environ.get("PHOTO", "tests/dasface/resources/face.jpg")
OTHER_PHOTO = os.environ.get("OTHER_PHOTO", "tests/dasface/resources/other_face.png")
VIDEO = os.environ.get("VIDEO", "tests/dasface/resources/face_video.mp4")
ANNOTATIONS = os.environ.get("ANNOTATIONS", "tests/dasface/resources/annotations.vtt")

client = DasfaceClient()

print(f"Alive: {client.alive()}")

# One entry per hash *and* mode, so the same hash appears several times.
models = client.get_models().models
print(f"Models offered: {[(m.hash[:12], m.mode, m.tag) for m in models]}")

# The model is part of the credential, so it has to be named: there is no endpoint that
# picks one. The newest default-mode model is the sensible choice.
model = max((m for m in models if m.mode == "default-mode"), key=lambda m: m.tag)
print(f"Using model {model.hash[:12]}… in {model.mode}, tag {model.tag}")

credential = client.generate_credential(image=PHOTO, hash=model.hash, mode=model.mode)
print(f"Credential generated: {credential.credential[:60]}…")
print(f"Model behind it: {client.get_model_metadata_from_credential(credential=credential.credential).metadata}")

# The photo can be bytes instead of a path, so nothing has to touch the filesystem.
with open(PHOTO, "rb") as f:
    from_bytes = client.generate_credential(image=f.read(), hash=model.hash, mode=model.mode)
print(f"Credential from bytes: {from_bytes.credential[:60]}…")

# Three ways to ask whether it is the same person.
print(f"Photo against photo: {client.verify_photo(anchor_image=PHOTO, target_image=PHOTO).confidence}")
print(f"Photo against a different person: {client.verify_photo(anchor_image=PHOTO, target_image=OTHER_PHOTO).confidence}")
print(f"Photo against video: {client.verify_video(anchor_image=PHOTO, target_video=VIDEO).confidence}")
against_credential = client.verify_credential(anchor_image=PHOTO, target_credential=credential.credential)
print(f"Photo against a credential: {against_credential.confidence}")

# Authenticity asks something else: whether the capture is genuine rather than a photo of a
# screen or a print.
print(f"Photo authenticity: {client.check_photo_authenticity(image=PHOTO).confidence}")

video_authenticity = client.check_video_authenticity(anchor_image=PHOTO, target_video=VIDEO)
print(f"Video authenticity: {video_authenticity.authenticity}, similarity: {video_authenticity.similarity}")

# A challenge asks something harder to fake: whether the recording was made *just now*, in
# response to instructions the recorder could not have known in advance.
challenge = client.generate_sequential_challenge(length=3)
print(f"Challenge {challenge.id} expires at {challenge.expires}")
for action in challenge.actions:
    print(f"  {action.name}: {action.action_class} {action.parameters}")

# Normally the token goes to the capture SDK, which returns the recording and its WebVTT
# annotations. Here both are stand-ins, so the confidence means nothing; what it shows is
# the shape of the call.
analysis = client.analyse_challenge_response(
    token=challenge.token,
    annotations=ANNOTATIONS,
    anchor_image=PHOTO,
    target_video=VIDEO,
)
if analysis.confidence is None:
    # This endpoint reports its failures inside a successful response, unlike every other.
    for error in analysis.errors:
        print(f"  could not analyse it: {error.code} — {error.message}")
else:
    print(f"Challenge analysis: {analysis.confidence}")
