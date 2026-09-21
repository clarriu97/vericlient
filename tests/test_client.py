import pytest
import requests_mock

from vericlient import DaspeakClient, VcspClient
from vericlient.apis import APIs
from vericlient.exceptions import ServerError
from vericlient.utils import DEFAULT_CONTENT_TYPE

VCSP_SANDBOX_EU = "https://api-work.eu.veri-das.com/vcsp/v1"

# The VCSP specification accepts all three spellings, and `mimetypes` picks a different
# one depending on the platform, so the tests assert membership rather than one value.
WAV_CONTENT_TYPES = {"audio/wav", "audio/wave", "audio/x-wav"}


def test_api_path_keeps_name_and_version_apart():
    assert APIs.DASPEAK.api_name == "daspeak"
    assert APIs.DASPEAK.version == "v1"
    assert APIs.DASPEAK.path == "daspeak/v1"
    assert APIs.VCSP.path == "vcsp/v1"


def test_client_url_is_built_from_the_api_path():
    assert DaspeakClient(apikey="fake-apikey").url.endswith("/daspeak/v1")
    assert VcspClient(apikey="fake-apikey").url.endswith("/vcsp/v1")


def test_delete_returns_the_response():
    """`_delete` used to fall off the end of the function and return None."""
    client = VcspClient(apikey="fake-apikey")
    with requests_mock.Mocker() as mock_server:
        mock_server.delete(f"{VCSP_SANDBOX_EU}/accounts/subject-1", status_code=204)
        response = client._delete(endpoint="accounts/subject-1")  # noqa: SLF001
    assert response is not None
    assert response.status_code == 204


def test_non_json_error_body_does_not_escape_as_a_decode_error():
    """A gateway can answer with HTML; that used to raise JSONDecodeError."""
    client = VcspClient(apikey="fake-apikey")
    with requests_mock.Mocker() as mock_server:
        mock_server.get(
            f"{VCSP_SANDBOX_EU}/alive",
            status_code=502,
            text="<html><body>Bad Gateway</body></html>",
        )
        with pytest.raises(ServerError):
            client.alive()


def test_get_sample_from_bytes_guesses_the_media_type(audio_file, audio_file_path):
    """The bytes branch used to call mimetypes.guess_type() with the bytes themselves."""
    client = VcspClient(apikey="fake-apikey")

    filename, content, content_type = client._get_sample(audio_file)  # noqa: SLF001
    assert filename == "sample"
    assert content == audio_file
    assert content_type in WAV_CONTENT_TYPES

    filename, _, content_type = client._get_sample(audio_file_path)  # noqa: SLF001
    assert filename == "audio.wav"
    assert content_type in WAV_CONTENT_TYPES


def test_get_sample_honours_an_explicit_media_type(audio_file):
    client = VcspClient(apikey="fake-apikey")
    _, _, content_type = client._get_sample(audio_file, "audio/x-wav")  # noqa: SLF001
    assert content_type == "audio/x-wav"


def test_get_sample_rejects_anything_else():
    client = VcspClient(apikey="fake-apikey")
    with pytest.raises(TypeError):
        client._get_sample(123)  # noqa: SLF001


def test_get_sample_falls_back_when_the_content_is_unknown():
    client = VcspClient(apikey="fake-apikey")
    _, _, content_type = client._get_sample(b"not a known format")  # noqa: SLF001
    assert content_type == DEFAULT_CONTENT_TYPE
