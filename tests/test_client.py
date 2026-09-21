import inspect

import pytest
import requests_mock
from pydantic import BaseModel, ValidationError

from vericlient import DaspeakClient, VcspClient
from vericlient.apis import APIs
from vericlient.config import DEFAULT_TIMEOUT
from vericlient.daspeak import models as daspeak_models
from vericlient.exceptions import ServerError
from vericlient.utils import DEFAULT_CONTENT_TYPE
from vericlient.vcsp import models as vcsp_models

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


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch) -> None:
    """Keep VERICLIENT_* out of the tests that do not set it themselves."""
    for name in ("APIKEY", "ENVIRONMENT", "LOCATION", "URL", "TIMEOUT"):
        monkeypatch.delenv(f"VERICLIENT_{name}", raising=False)


def test_explicit_arguments_win_over_the_environment(monkeypatch):
    """The old behaviour was the other way round: the environment silently won."""
    monkeypatch.setenv("VERICLIENT_APIKEY", "from-env")
    monkeypatch.setenv("VERICLIENT_ENVIRONMENT", "production")
    monkeypatch.setenv("VERICLIENT_LOCATION", "us")
    monkeypatch.setenv("VERICLIENT_TIMEOUT", "99")

    client = DaspeakClient(apikey="explicit", environment="sandbox", location="eu", timeout=5)

    assert client.headers["apikey"] == "explicit"
    assert client.url == "https://api-work.eu.veri-das.com/daspeak/v1"
    assert client.timeout == 5


def test_the_environment_fills_in_what_the_caller_left_out(monkeypatch):
    monkeypatch.setenv("VERICLIENT_APIKEY", "from-env")
    monkeypatch.setenv("VERICLIENT_ENVIRONMENT", "production")
    monkeypatch.setenv("VERICLIENT_LOCATION", "us")
    monkeypatch.setenv("VERICLIENT_TIMEOUT", "99")

    client = DaspeakClient()

    assert client.headers["apikey"] == "from-env"
    assert client.url == "https://api.us.veri-das.com/daspeak/v1"
    assert client.timeout == 99


def test_defaults_apply_when_nothing_is_given():
    client = DaspeakClient(apikey="explicit")
    assert client.url == "https://api-work.eu.veri-das.com/daspeak/v1"
    assert client.timeout == DEFAULT_TIMEOUT


def test_an_explicit_url_wins_over_the_environment(monkeypatch):
    monkeypatch.setenv("VERICLIENT_URL", "https://from-env.example.com")
    assert DaspeakClient(url="https://explicit.example.com").url == "https://explicit.example.com"


def test_a_self_hosted_url_needs_no_apikey(monkeypatch):
    monkeypatch.setenv("VERICLIENT_URL", "https://self-hosted.example.com")
    client = DaspeakClient()
    assert client.url == "https://self-hosted.example.com"
    assert "apikey" not in client.headers


def test_a_cloud_client_without_an_apikey_is_refused():
    with pytest.raises(ValueError, match="apikey must be provided"):
        DaspeakClient()


def test_a_malformed_timeout_in_the_environment_is_reported(monkeypatch):
    """Dynaconf passed the string through; the value only blew up at request time."""
    monkeypatch.setenv("VERICLIENT_TIMEOUT", "not-a-number")
    with pytest.raises(ValidationError):
        DaspeakClient(apikey="explicit")


def test_two_clients_can_use_different_keys():
    daspeak = DaspeakClient(apikey="key-one")
    vcsp = VcspClient(apikey="key-two")
    assert daspeak.headers["apikey"] == "key-one"
    assert vcsp.headers["apikey"] == "key-two"


def test_no_response_model_exposes_the_http_status_code():
    """The status code is an HTTP detail and has no place on a service client's response.

    Written generically on purpose: a new output model that copies the old pattern fails
    here rather than shipping.
    """
    offenders = [
        f"{module.__name__}.{name}"
        for module in (daspeak_models, vcsp_models)
        for name, obj in vars(module).items()
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and "status_code" in obj.model_fields
    ]
    assert not offenders, f"these models still carry the HTTP status code: {offenders}"
