"""Example script showing how to use the das-Peak client.

Runnable as it stands: it defaults to the repository's own test recording, so
`pdm run python scripts/daspeak.py` works in a checkout. Point `AUDIO` at your own file to
use a different one. It needs `VERICLIENT_APIKEY` in the environment.
"""

import os

from vericlient import DaspeakClient

AUDIO = os.environ.get("AUDIO", "tests/daspeak/resources/audio.wav")

client = DaspeakClient()

print(f"Alive: {client.alive()}")

# One entry per biometrics model the service offers.
models = client.get_models().models
print(f"Biometrics models: {models}")

model = models[-1]
print(f"Model metadata: {client.get_model_metadata(hash=model).metadata}")
print(f"Calibrations it supports: {client.get_model_calibrations(hash=model).calibrations}")

# A credential is the biometric representation of a voice. The audio can be a path...
credential = client.generate_credential(audio=AUDIO, hash=model).credential
print(f"Credential generated from a path: {credential}")

# ...or the content itself, so nothing has to touch the filesystem.
with open(AUDIO, "rb") as f:
    from_bytes = client.generate_credential(audio=f.read(), hash=model).credential
print(f"Credential generated from bytes: {from_bytes}")

print(f"Model behind the credential: {client.get_model_metadata_from_credential(credential=credential).metadata}")

# The everyday verification: a stored credential against a fresh recording.
comparison = client.compare_credential_to_audio(credential_reference=credential, audio_to_evaluate=AUDIO)
print(f"Credential against audio: {comparison.score}")
print(f"  authenticity: {comparison.authenticity_to_evaluate}")
print(f"  net speech duration: {comparison.net_speech_duration_to_evaluate}")

# Two recordings directly, without enrolling either of them first.
with open(AUDIO, "rb") as f:
    comparison = client.compare_audio_to_audio(audio_reference=AUDIO, audio_to_evaluate=f.read())
print(f"Audio against audio: {comparison.score}")
print(f"  authenticity of the reference: {comparison.authenticity_reference}")
print(f"  authenticity of the evaluated: {comparison.authenticity_to_evaluate}")

comparison = client.compare_credential_to_credential(
    credential_reference=credential,
    credential_to_evaluate=credential,
)
print(f"Credential against credential: {comparison.score}")

# One against many, where everything above is one against one.
identification = client.identify_audio(
    audio_to_evaluate=AUDIO,
    credential_list=[("subject-1", credential), ("subject-2", from_bytes)],
)
print(f"Identified from audio: {identification.scores}")

identification = client.identify_credential(
    credential_to_evaluate=credential,
    credential_list=[("subject-1", credential), ("subject-2", from_bytes)],
)
print(f"Identified from a credential: {identification.scores}")
