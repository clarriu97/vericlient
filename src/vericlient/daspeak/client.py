"""Implementation of the client for the DASPEaK service."""
import json

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
    CompareAudio2CredentialsInput,
    CompareAudio2CredentialsOutput,
    CompareCredential2AudioInput,
    CompareCredential2AudioOutput,
    CompareCredential2CredentialInput,
    CompareCredential2CredentialOutput,
    CompareCredential2CredentialsInput,
    CompareCredential2CredentialsOutput,
    CompareInput,
    GenerateCredentialInput,
    GenerateCredentialOutput,
    ModelsOutput,
)
from vericlient.exceptions import InvalidCredentialError, UnsupportedMediaTypeError


class DaspeakClient(Client):
    """Class to interact with the Daspeak API."""

    def __init__(
            self,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the DaspeakClient class.

        Args:
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        api = APIs.DASPEAK.value
        super().__init__(
            api=api,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        self._exceptions = [
            "AudioInputException",
            "SignalNoiseRatioException",
            "VoiceDurationIsNotEnoughException",
            "InvalidChannelException",
            "InsufficientQuality",
            "CalibrationNotAvailable",
            "ServerError",
            "InvalidCredential",
            "UnsupportedMediaType",
        ]
        self._compare_functions_map = {
            CompareCredential2AudioInput: self._compare_credential2audio,
            CompareAudio2AudioInput: self._compare_audio2audio,
            CompareCredential2CredentialInput: self._compare_credential2credential,
            CompareAudio2CredentialsInput: self._compare_audio2credentials,
            CompareCredential2CredentialsInput: self._compare_credential2credentials,
        }

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=DaspeakEndpoints.ALIVE.value)
        accepted_status_code = 200
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:   # noqa: C901, PLR0912
        """Handle error responses from the API."""
        response_json = response.json()
        if response_json["exception"] not in self._exceptions:
            self._raise_server_error(response)
        if response_json["exception"] == "AudioInputException":
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
            error = response_json["error"]
            calibration = str(error.split(" ")[2])
            raise CalibrationNotAvailableError(calibration)
        if response_json["exception"] == "InvalidCredential":
            raise InvalidCredentialError
        if response_json["exception"] == "UnsupportedMediaType":
            raise UnsupportedMediaTypeError
        raise ValueError(response_json["error"])

    def get_models(self) -> ModelsOutput:
        """Get the models available biometrics models in the service.

        Returns:
            The response from the service

        """
        response = self._get(endpoint=DaspeakEndpoints.MODELS.value)
        return ModelsOutput(status_code=response.status_code, **response.json())

    def generate_credential(self, data_model: GenerateCredentialInput) -> GenerateCredentialOutput:
        """Generate a credential from a WAV file.

        Args:
            data_model: The data required to generate the credential

        Returns:
            The response from the service

        Raises:
            ValueError: If the `data_model` is not an instance of `GenerateCredentialInput`
            TooManyAudioChannelsError: If the audio has more channels than the service supports
            UnsupportedAudioCodecError: If the audio has an unsupported codec
            UnsupportedSampleRateError: If the audio has an unsupported sample rate
            AudioDurationTooLongError: If the audio duration is longer than the service supports
            SignalNoiseRatioError: If the signal-to-noise ratio is too low
            NetSpeechDurationIsNotEnoughError: If the net speech duration is not enough
            InvalidSpecifiedChannelError: If the specified channel is invalid
            InsufficientQualityError: If the audio quality is insufficient
            CalibrationNotAvailableError: If the calibration is not available
            UnsupportedMediaTypeError: If the media type is not supported

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
        return GenerateCredentialOutput(status_code=response.status_code, **response.json())

    def compare(    # noqa: D417
            self,
            data_model: CompareInput,
        ) -> CompareCredential2AudioOutput | CompareAudio2AudioOutput | \
             CompareCredential2CredentialOutput | CompareAudio2CredentialsOutput | \
             CompareCredential2CredentialsOutput:
        """Compare two sets of data based on the provided input.

        Args:
            data_model (CompareCredential2AudioInput | CompareAudio2AudioInput | CompareCredential2CredentialInput | \
                        CompareAudio2CredentialsInput | CompareCredential2CredentialsInput):
                The data required to compare the audio files or credentials

        Returns:
            The response from the service, depending on the input type.

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
            InvalidCredentialError: If the credential is invalid
            UnsupportedMediaTypeError: If the media type is not supported

        """
        try:
            func = self._compare_functions_map.get(type(data_model))
            return func(data_model)
        except AttributeError as e:
            error = "data_model must be an instance of CompareInput"
            raise TypeError(error) from e

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

    def _compare_credential2credential(
            self,
            data_model: CompareCredential2CredentialInput,
        ) -> CompareCredential2CredentialOutput:
        """Compare two credentials.

        Args:
            data_model: The data required to compare the credentials

        Returns:
            CompareCredential2CredentialOutput: The response from the service

        """
        endpoint = DaspeakEndpoints.SIMILARITY_CREDENTIAL2CREDENTIAL.value
        data = {
            "credential_reference": data_model.credential_reference,
            "credential_to_evaluate": data_model.credential_to_evaluate,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data)
        return CompareCredential2CredentialOutput(status_code=response.status_code, **response.json())

    def _compare_audio2credentials(
        self,
        data_model: CompareAudio2CredentialsInput,
    ) -> CompareAudio2CredentialsOutput:
        """Compare an audio file with a list of credentials.

        Args:
            data_model: The data required to compare the audio file with the credentials

        Returns:
            CompareAudio2CredentialsOutput: The response from the service

        """
        endpoint = DaspeakEndpoints.IDENTIFICATION_AUDIO2CREDENTIALS.value
        audio = self._get_virtual_audio_file(data_model.audio_reference)
        files = {
            "audio_reference": ("audio_reference", audio, "audio/wav"),
        }
        credential_list = json.dumps(data_model.credential_list)
        data = {
            "credential_list": credential_list,
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareAudio2CredentialsOutput(status_code=response.status_code, **response.json())

    def _compare_credential2credentials(
        self,
        data_model: CompareCredential2CredentialsInput,
    ) -> CompareCredential2CredentialsOutput:
        endpoint = DaspeakEndpoints.IDENTIFICATION_CREDENTIAL2CREDENTIALS.value
        credential_list = json.dumps(data_model.credential_list)
        data = {
            "credential_reference": data_model.credential_reference,
            "credential_list": credential_list,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data)
        return CompareCredential2CredentialsOutput(status_code=response.status_code, **response.json())

    def _get_virtual_audio_file(self, audio_input: object) -> bytes:
        if isinstance(audio_input, str):
            try:
                with open(audio_input, "rb") as f:
                    audio = f.read()
            except FileNotFoundError as e:
                error = f"File {audio_input} not found"
                raise FileNotFoundError(error) from e
        elif isinstance(audio_input, bytes):
            audio = audio_input
        else:
            error = "audio must be a string or a bytes object"
            raise TypeError(error)
        return audio
