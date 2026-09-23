"""Implementation of the client for the DASPEaK service."""

import json
import warnings

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.daspeak.endpoints import DaspeakEndpoints
from vericlient.daspeak.exceptions import (
    AudioDurationTooLongError,
    CalibrationNotAvailableError,
    InsufficientQualityError,
    InvalidSpecifiedChannelError,
    ModelNotAvailableError,
    NetSpeechDurationIsNotEnoughError,
    SignalNoiseRatioError,
    TooManyAudioChannelsError,
    UnsupportedAudioCodecError,
    UnsupportedSampleRateError,
    VeriClientError,
)
from vericlient.daspeak.models import (
    DEFAULT_CALIBRATION,
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
    GetModelCalibrationsInput,
    GetModelCalibrationsOutput,
    GetModelMetadataFromCredentialInput,
    GetModelMetadataFromCredentialOutput,
    GetModelMetadataInput,
    GetModelMetadataOutput,
    ModelsOutput,
)
from vericlient.deprecation import legacy_model_argument
from vericlient.exceptions import InvalidCredentialError, UnsupportedMediaTypeError
from vericlient.utils import get_virtual_file


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
        api = APIs.DASPEAK
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
            "ModelNotAvailable",
        ]
        # Only `compare()` reads this, and `compare()` is deprecated: each of these has a
        # method of its own now.
        self._compare_functions_map = {
            CompareCredential2AudioInput: self.compare_credential_to_audio,
            CompareAudio2AudioInput: self.compare_audio_to_audio,
            CompareCredential2CredentialInput: self.compare_credential_to_credential,
            CompareAudio2CredentialsInput: self.identify_audio,
            CompareCredential2CredentialsInput: self.identify_credential,
        }
        self._exception_map = {
            "SignalNoiseRatioException": SignalNoiseRatioError,
            "VoiceDurationIsNotEnoughException": self._handle_voice_duration_error,
            "InvalidChannelException": InvalidSpecifiedChannelError,
            "InsufficientQuality": InsufficientQualityError,
            "CalibrationNotAvailable": self._handle_calibration_error,
            "InvalidCredential": InvalidCredentialError,
            "UnsupportedMediaType": UnsupportedMediaTypeError,
            "ModelNotAvailable": self._handle_model_not_available_error,
        }
        self._audio_input_errors = {
            "more channels than": TooManyAudioChannelsError,
            "unsupported codec": UnsupportedAudioCodecError,
            "sample rate": UnsupportedSampleRateError,
            "duration is longer": AudioDurationTooLongError,
        }

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=DaspeakEndpoints.ALIVE.value)
        accepted_status_code = 200
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API."""
        response_json = self._error_payload(response)

        exception = response_json.get("exception")
        if not exception or exception not in self._exceptions:
            self._raise_server_error(response)

        if exception == "AudioInputException":
            error_message = response_json.get("error", "")
            for error_text, error_class in self._audio_input_errors.items():
                if error_text in error_message:
                    raise error_class
            raise ValueError(error_message)

        handler = self._exception_map.get(exception)
        if handler:
            if isinstance(handler, type) and issubclass(handler, VeriClientError):
                raise handler
            handler(response_json)

        raise ValueError(response_json.get("error", "Unknown error"))

    def _handle_voice_duration_error(self, response_json: dict) -> None:
        error_message = response_json.get("error", "")
        net_speech_detected = float(error_message.split(" ")[-3].replace("s", ""))
        raise NetSpeechDurationIsNotEnoughError(net_speech_detected)

    def _handle_model_not_available_error(self, response_json: dict) -> None:
        error_message = response_json.get("error", "")
        model_hash = error_message.rsplit(" ", 1)[-1]
        raise ModelNotAvailableError(model_hash)

    def _handle_calibration_error(self, response_json: dict) -> None:
        error_message = response_json.get("error", "")
        calibration = str(error_message.split(" ")[2])
        raise CalibrationNotAvailableError(calibration)

    def get_models(self) -> ModelsOutput:
        """Get the models available biometrics models in the service.

        Returns:
            The response from the service

        """
        response = self._get(endpoint=DaspeakEndpoints.MODELS.value)
        return ModelsOutput(**response.json())

    @legacy_model_argument(GetModelMetadataInput)
    def get_model_metadata(self, hash: str) -> GetModelMetadataOutput:  # noqa: A002
        """Get the metadata of a biometrics model.

        Args:
            hash: The hash of the model to describe

        Returns:
            The response from the service

        Raises:
            ModelNotAvailableError: If no model exists with that hash

        """
        data_model = GetModelMetadataInput(hash=hash)
        response = self._post(
            endpoint=DaspeakEndpoints.MODELS_METADATA.value,
            data={"hash": data_model.hash},
        )
        return GetModelMetadataOutput(**response.json())

    @legacy_model_argument(GetModelCalibrationsInput)
    def get_model_calibrations(self, hash: str) -> GetModelCalibrationsOutput:  # noqa: A002
        """Get the calibration modes a biometrics model supports.

        Any of the returned values is valid as the `calibration` argument of
        `generate_credential` and of the comparison inputs.

        Args:
            hash: The hash of the model to list the calibrations of

        Returns:
            The response from the service

        Raises:
            ModelNotAvailableError: If no model exists with that hash

        """
        data_model = GetModelCalibrationsInput(hash=hash)
        response = self._post(
            endpoint=DaspeakEndpoints.MODELS_CALIBRATION.value,
            data={"hash": data_model.hash},
        )
        return GetModelCalibrationsOutput(**response.json())

    @legacy_model_argument(GetModelMetadataFromCredentialInput)
    def get_model_metadata_from_credential(self, credential: str) -> GetModelMetadataFromCredentialOutput:
        """Get the metadata of the model a credential was generated with.

        Useful to find out whether a stored credential is still compatible with the models
        the service currently offers.

        Args:
            credential: The credential to read the originating model from

        Returns:
            The response from the service

        Raises:
            InvalidCredentialError: If the credential is not valid

        """
        data_model = GetModelMetadataFromCredentialInput(credential=credential)
        response = self._post(
            endpoint=DaspeakEndpoints.MODELS_METADATA_FROM_CREDENTIAL.value,
            data={"credential": data_model.credential},
        )
        return GetModelMetadataFromCredentialOutput(**response.json())

    @legacy_model_argument(GenerateCredentialInput)
    def generate_credential(
        self,
        audio: str | bytes,
        hash: str,  # noqa: A002
        channel: int = 1,
        calibration: str = DEFAULT_CALIBRATION,
    ) -> GenerateCredentialOutput:
        """Generate a credential from a WAV file.

        Args:
            audio: The recording, as a path or as bytes
            hash: The hash of the biometrics model to use, from `get_models()`
            channel: Which channel to read, when the recording is stereo
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            The response from the service

        Raises:
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
        data_model = GenerateCredentialInput(audio=audio, hash=hash, channel=channel, calibration=calibration)
        endpoint = DaspeakEndpoints.MODELS_HASH_CREDENTIAL_AUDIO.value.replace("<hash>", data_model.hash)
        audio = get_virtual_file(data_model.audio)
        files = {
            "audio": ("audio", audio, "audio/wav"),
        }
        data = {
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return GenerateCredentialOutput(**response.json())

    def compare(
        self,
        data_model: CompareInput,
    ) -> (
        CompareCredential2AudioOutput
        | CompareAudio2AudioOutput
        | CompareCredential2CredentialOutput
        | CompareAudio2CredentialsOutput
        | CompareCredential2CredentialsOutput
    ):
        """Compare two sets of data, dispatching on the type of the input model.

        Deprecated, and removed in 1.0.0. There are five comparisons behind this one method
        and the only way to pick between them was to pass one of five classes, so it could
        not be called at all without importing one. Each has a method of its own now:

        | This model | That method |
        |---|---|
        | `CompareCredential2AudioInput` | `compare_credential_to_audio` |
        | `CompareAudio2AudioInput` | `compare_audio_to_audio` |
        | `CompareCredential2CredentialInput` | `compare_credential_to_credential` |
        | `CompareAudio2CredentialsInput` | `identify_audio` |
        | `CompareCredential2CredentialsInput` | `identify_credential` |

        Args:
            data_model: One of the five comparison inputs

        Returns:
            The response from the service, of the kind matching the input

        Raises:
            TypeError: If `data_model` is not one of the five comparison inputs

        """
        method = self._compare_functions_map.get(type(data_model))
        if method is None:
            error = "data_model must be an instance of CompareInput"
            raise TypeError(error)

        warnings.warn(
            f"compare() is deprecated and will be removed in 1.0.0. Call {method.__name__}() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return method(**dict(data_model))

    @legacy_model_argument(CompareCredential2AudioInput)
    def compare_credential_to_audio(
        self,
        credential_reference: str,
        audio_to_evaluate: str | bytes,
        channel: int = 1,
        calibration: str = DEFAULT_CALIBRATION,
    ) -> CompareCredential2AudioOutput:
        """Compare a stored credential against a recording.

        The everyday verification: enrol once into a credential, then check later recordings
        against it without keeping the original audio.

        Args:
            credential_reference: The stored credential
            audio_to_evaluate: The recording to check, as a path or as bytes
            channel: Which channel to read, when the recording is stereo
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            CompareCredential2AudioOutput: The score, and whether it passes

        Raises:
            InvalidCredentialError: If the credential is not valid
            NetSpeechDurationIsNotEnoughError: If the recording holds too little speech
            CalibrationNotAvailableError: If the calibration is not available

        """
        data_model = CompareCredential2AudioInput(
            credential_reference=credential_reference,
            audio_to_evaluate=audio_to_evaluate,
            channel=channel,
            calibration=calibration,
        )
        endpoint = DaspeakEndpoints.SIMILARITY_CREDENTIAL2AUDIO.value
        audio = get_virtual_file(data_model.audio_to_evaluate)
        files = {
            "audio_to_evaluate": ("audio", audio, "audio/wav"),
        }
        data = {
            "credential_reference": data_model.credential_reference,
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareCredential2AudioOutput(**response.json())

    @legacy_model_argument(CompareAudio2AudioInput)
    def compare_audio_to_audio(
        self,
        audio_reference: str | bytes,
        audio_to_evaluate: str | bytes,
        channel_reference: int = 1,
        channel_to_evaluate: int = 1,
        calibration: str = DEFAULT_CALIBRATION,
    ) -> CompareAudio2AudioOutput:
        """Compare two recordings directly, without generating a credential first.

        Args:
            audio_reference: The reference recording, as a path or as bytes
            audio_to_evaluate: The recording to check, as a path or as bytes
            channel_reference: Which channel of the reference to read
            channel_to_evaluate: Which channel of the recording to check
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            CompareAudio2AudioOutput: The score, and whether it passes

        Raises:
            NetSpeechDurationIsNotEnoughError: If either recording holds too little speech
            SignalNoiseRatioError: If either recording is too noisy
            CalibrationNotAvailableError: If the calibration is not available

        """
        data_model = CompareAudio2AudioInput(
            audio_reference=audio_reference,
            audio_to_evaluate=audio_to_evaluate,
            channel_reference=channel_reference,
            channel_to_evaluate=channel_to_evaluate,
            calibration=calibration,
        )
        endpoint = DaspeakEndpoints.SIMILARITY_AUDIO2AUDIO.value
        files = {
            "audio_reference": ("audio", get_virtual_file(data_model.audio_reference), "audio/wav"),
            "audio_to_evaluate": ("audio", get_virtual_file(data_model.audio_to_evaluate), "audio/wav"),
        }
        data = {
            "channel_reference": data_model.channel_reference,
            "channel_to_evaluate": data_model.channel_to_evaluate,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareAudio2AudioOutput(**response.json())

    @legacy_model_argument(CompareCredential2CredentialInput)
    def compare_credential_to_credential(
        self,
        credential_reference: str,
        credential_to_evaluate: str,
        calibration: str = DEFAULT_CALIBRATION,
    ) -> CompareCredential2CredentialOutput:
        """Compare two stored credentials.

        Args:
            credential_reference: The reference credential
            credential_to_evaluate: The credential to check against it
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            CompareCredential2CredentialOutput: The score, and whether it passes

        Raises:
            InvalidCredentialError: If either credential is not valid
            CalibrationNotAvailableError: If the calibration is not available

        """
        data_model = CompareCredential2CredentialInput(
            credential_reference=credential_reference,
            credential_to_evaluate=credential_to_evaluate,
            calibration=calibration,
        )
        endpoint = DaspeakEndpoints.SIMILARITY_CREDENTIAL2CREDENTIAL.value
        data = {
            "credential_reference": data_model.credential_reference,
            "credential_to_evaluate": data_model.credential_to_evaluate,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data)
        return CompareCredential2CredentialOutput(**response.json())

    @legacy_model_argument(CompareAudio2CredentialsInput)
    def identify_audio(
        self,
        audio_to_evaluate: str | bytes,
        credential_list: list[tuple[str, str]],
        channel: int = 1,
        calibration: str = DEFAULT_CALIBRATION,
    ) -> CompareAudio2CredentialsOutput:
        """Find which of several credentials a recording belongs to.

        One against many, where the comparison methods are one against one.

        Args:
            audio_to_evaluate: The recording to identify, as a path or as bytes
            credential_list: The candidates, as `(identifier, credential)` pairs
            channel: Which channel to read, when the recording is stereo
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            CompareAudio2CredentialsOutput: A score per candidate

        Raises:
            InvalidCredentialError: If a credential is not valid
            NetSpeechDurationIsNotEnoughError: If the recording holds too little speech

        """
        data_model = CompareAudio2CredentialsInput(
            audio_to_evaluate=audio_to_evaluate,
            credential_list=credential_list,
            channel=channel,
            calibration=calibration,
        )
        endpoint = DaspeakEndpoints.IDENTIFICATION_AUDIO2CREDENTIALS.value
        files = {
            "audio_to_evaluate": ("audio", get_virtual_file(data_model.audio_to_evaluate), "audio/wav"),
        }
        data = {
            "credential_list": json.dumps(data_model.credential_list),
            "channel": data_model.channel,
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        return CompareAudio2CredentialsOutput(**response.json())

    @legacy_model_argument(CompareCredential2CredentialsInput)
    def identify_credential(
        self,
        credential_to_evaluate: str,
        credential_list: list[tuple[str, str]],
        calibration: str = DEFAULT_CALIBRATION,
    ) -> CompareCredential2CredentialsOutput:
        """Find which of several credentials another credential belongs to.

        Args:
            credential_to_evaluate: The credential to identify
            credential_list: The candidates, as `(identifier, credential)` pairs
            calibration: The calibration to use, from `get_model_calibrations()`

        Returns:
            CompareCredential2CredentialsOutput: A score per candidate

        Raises:
            InvalidCredentialError: If a credential is not valid
            CalibrationNotAvailableError: If the calibration is not available

        """
        data_model = CompareCredential2CredentialsInput(
            credential_to_evaluate=credential_to_evaluate,
            credential_list=credential_list,
            calibration=calibration,
        )
        endpoint = DaspeakEndpoints.IDENTIFICATION_CREDENTIAL2CREDENTIALS.value
        data = {
            "credential_to_evaluate": data_model.credential_to_evaluate,
            "credential_list": json.dumps(data_model.credential_list),
            "calibration": data_model.calibration,
        }
        response = self._post(endpoint=endpoint, data=data)
        return CompareCredential2CredentialsOutput(**response.json())
