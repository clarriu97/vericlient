"""Implementation of the client for the DASPEaK service."""
from io import BytesIO

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.daspeak.endpoints import DaspeakEndpoints
from vericlient.daspeak.exceptions import (
    AudioDurationTooLongError,
    CalibrationNotAvailableError,
    InsufficientQualityError,
    InvalidSpecifiedChannelError,
    NetSpeechDurationIsNotEnoughError,
    SignalNoiseRatioError,
    TooManyAudioChannelsError,
    UnsupportedAudioCodecError,
    UnsupportedSampleRateError,
)
from vericlient.daspeak.models import (
    CompareAudio2AudioInput,
    CompareAudio2AudioOutput,
    CompareCredential2AudioInput,
    CompareCredential2AudioOutput,
    CompareInput,
    ModelsHashCredentialAudioInput,
    ModelsHashCredentialAudioOutput,
    ModelsOutput,
)


class DaspeakClient(Client):
    """Class to interact with the Daspeak API."""

    def __init__(
            self,
            api: str = APIs.DASPEAK.value,
            apikey: str | None = None,
            target: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the DaspeakClient class.

        Args:
            api: The API to use
            apikey: The API key to use
            target: The target to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        super().__init__(
            api=api,
            apikey=apikey,
            target=target,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        self._exceptions = [
            "InputException",
            "SignalNoiseRatioException",
            "VoiceDurationIsNotEnoughException",
            "InvalidChannelException",
            "InsufficientQuality",
            "CalibrationNotAvailable",
            "ServerError",
        ]

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=DaspeakEndpoints.ALIVE.value)
        accepted_status_code = 200
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:   # noqa: C901
        """Handle error responses from the API."""
        response_json = response.json()
        if response_json["exception"] not in self._exceptions:
            self._raise_server_error(response)
        if response_json["exception"] == "InputException":
            if "more channels than" in response_json["error"]:
                raise TooManyAudioChannelsError
            if "unsupported codec" in response_json["error"]:
                raise UnsupportedAudioCodecError
            if "sample rate" in response_json["error"]:
                raise UnsupportedSampleRateError
            if "duration is longer" in response_json["error"]:
                raise AudioDurationTooLongError
            raise ValueError(response_json["error"])
        if response_json["exception"] == "SignalNoiseRatioException":
            raise SignalNoiseRatioError
        if response_json["exception"] == "VoiceDurationIsNotEnoughException":
            error = response_json["error"]
            net_speech_detected = float(error.split(" ")[-3].replace("s", ""))
            raise NetSpeechDurationIsNotEnoughError(net_speech_detected)
        if response_json["exception"] == "InvalidChannelException":
            raise InvalidSpecifiedChannelError
        if response_json["exception"] == "InsufficientQuality":
            raise InsufficientQualityError
        if response_json["exception"] == "CalibrationNotAvailable":
            raise CalibrationNotAvailableError
        raise ValueError(response_json["error"])

    def get_models(self) -> ModelsOutput:
        """Get the models available biometrics models in the service.

        Returns:
            The response from the service

        """
        response = self._get(endpoint=DaspeakEndpoints.MODELS.value)
        return ModelsOutput(status_code=response.status_code, **response.json())

    def generate_credential(self, data_model: ModelsHashCredentialAudioInput) -> ModelsHashCredentialAudioOutput:
        """Generate a credential from a WAV file.

        Args:
            data_model: The data required to generate the credential

        Returns:
            The response from the service

        """
        endpoint = DaspeakEndpoints.MODELS_HASH_CREDENTIAL_AUDIO.value.replace("<hash>", data_model.hash)
        audio = self._get_virtual_audio_file(data_model.audio)
        files = {
            "audio": ("audio", audio, "audio/wav"),
        }
        data = {
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return ModelsHashCredentialAudioOutput(status_code=response.status_code, **response.json())

    def compare(
            self,
            data_model: CompareInput,
        ) -> CompareCredential2AudioOutput | CompareAudio2AudioOutput:
        """Compare audio files or credentials.

        Args:
            data_model (CompareCredential2AudioInput | CompareAudio2AudioInput):
                The data required to compare the audio files or credentials

        Returns:
            (CompareCredential2AudioOutput | CompareAudio2AudioOutput): The response from the service,
                depending on the input type.

        Raises:
            ValueError: If the `data_model` is not an instance of `CompareInput`
            TooManyAudioChannelsError: If the audio has more channels than the service supports
            UnsupportedAudioCodecError: If the audio has an unsupported codec
            UnsupportedSampleRateError: If the audio has an unsupported sample rate
            AudioDurationTooLongError: If the audio duration is longer than the service supports
            SignalNoiseRatioError: If the signal-to-noise ratio is too low
            NetSpeechDurationIsNotEnoughError: If the net speech duration is not enough
            InvalidSpecifiedChannelError: If the specified channel is invalid
            InsufficientQualityError: If the audio quality is insufficient
            CalibrationNotAvailableError: If the calibration is not available

        """
        if isinstance(data_model, CompareCredential2AudioInput):
            return self._compare_credential2audio(data_model)
        if isinstance(data_model, CompareAudio2AudioInput):
            return self._compare_audio2audio(data_model)
        error = "data_model must be an instance of CompareInput"
        raise ValueError(error)

    def _compare_credential2audio(
            self,
            data_model: CompareCredential2AudioInput,
        ) -> CompareCredential2AudioOutput:
        """Compare a credential with an audio file.

        Args:
            data_model: The data required to compare the credential with the audio

        Returns:
            CompareCredential2AudioOutput: The response from the service

        """
        endpoint = DaspeakEndpoints.SIMILARITY_CREDENTIAL2AUDIO.value
        audio = self._get_virtual_audio_file(data_model.audio_to_evaluate)
        files = {
            "audio_to_evaluate": ("audio", audio, "audio/wav"),
        }
        data = {
            "credential_reference": data_model.credential_reference,
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareCredential2AudioOutput(status_code=response.status_code, **response.json())

    def _compare_audio2audio(self, data_model: CompareAudio2AudioInput) -> CompareAudio2AudioOutput:
        """Compare two audio files.

        Args:
            data_model: The data required to compare the audio files

        Returns:
            CompareAudio2AudioOutput: The response from the service

        """
        endpoint = DaspeakEndpoints.SIMILARITY_AUDIO2AUDIO.value
        audio_reference = self._get_virtual_audio_file(data_model.audio_reference)
        audio_to_evaluate = self._get_virtual_audio_file(data_model.audio_to_evaluate)
        files = {
            "audio_reference": ("audio", audio_reference, "audio/wav"),
            "audio_to_evaluate": ("audio", audio_to_evaluate, "audio/wav"),
        }
        data = {
            "channel_reference": data_model.channel_reference,
            "channel_to_evaluate": data_model.channel_to_evaluate,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareAudio2AudioOutput(status_code=response.status_code, **response.json())

    def _get_virtual_audio_file(self, audio_input: object) -> BytesIO:
        if isinstance(audio_input, str):
            try:
                with open(audio_input, "rb") as f:
                    audio = f.read()
            except FileNotFoundError as e:
                error = f"File {audio_input} not found"
                raise FileNotFoundError(error) from e
        elif isinstance(audio_input, BytesIO):
            audio = audio_input.read()
            audio_input.close()
        else:
            error = "audio must be a string or a BytesIO object"
            raise TypeError(error)
        return audio
