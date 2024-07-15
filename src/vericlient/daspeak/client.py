"""
Implementation of the client for the DASPEaK service.
"""
from io import BytesIO

import requests
from requests.models import Response as Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.daspeak.endpoints import DaspeakEndpoints
from vericlient.daspeak.models import (
    ModelsOutput,
    ModelsHashCredentialWavInput,
    ModelsHashCredentialWavOutput
)
from vericlient.daspeak.exceptions import (
    TooManyAudioChannelsError,
    UnsupportedAudioCodecError,
    UnsupportedSampleRateError,
    AudioDurationTooLongError,
    SignalNoiseRatioError,
    NetSpeechDurationIsNotEnoughError,
    InvalidSpecifiedChannelError,
    CalibrationNotAvailableError,
    InsufficientQualityError
)


class DaspeakClient(Client):
    """
    Class to interact with the Daspeak API
    """
    def __init__(
            self,
            api: str = APIs.DASPEAK.value,
            apikey: str = None,
            target: str = None,
            timeout: int = None,
            environment: str = None,
            location: str = None,
            url: str = None,
            headers: dict = None,
    ) -> None:
        """
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
            "ServerError"
        ]

    def alive(self) -> bool:
        """
        Check if the service is alive.
        
        Returns:
            bool: True if the service is alive, False otherwise
        """
        response = self._get(endpoint=DaspeakEndpoints.ALIVE.value)
        return response.status_code == 200

    def _handle_error_response(self, response: Response):
        """
        Method to handle error responses from the API.
        """
        self._handle_authorization_error(response)
        response_json = response.json()
        if response_json["exception"] not in self._exceptions:
            self._raise_server_error(response)
        if response_json["exception"] == "InputException":
            if "more channels than" in response_json["error"]:
                raise TooManyAudioChannelsError()
            elif "unsupported codec" in response_json["error"]:
                raise UnsupportedAudioCodecError()
            elif "sample rate" in response_json["error"]:
                raise UnsupportedSampleRateError()
            elif "duration is longer" in response_json["error"]:
                raise AudioDurationTooLongError()
            else:
                raise ValueError(response_json["error"])
        elif response_json["exception"] == "SignalNoiseRatioException":
            raise SignalNoiseRatioError()
        elif response_json["exception"] == "VoiceDurationIsNotEnoughException":
            error = response_json["error"]
            net_speech_detected = float(error.split(" ")[-3].replace("s", ""))
            raise NetSpeechDurationIsNotEnoughError(net_speech_detected)
        elif response_json["exception"] == "InvalidChannelException":
            raise InvalidSpecifiedChannelError()
        elif response_json["exception"] == "InsufficientQuality":
            raise InsufficientQualityError()
        elif response_json["exception"] == "CalibrationNotAvailable":
            raise CalibrationNotAvailableError()
        else:
            raise ValueError(response_json["error"])

    def get_models(self) -> ModelsOutput:
        """
        Get the models available biometrics models in the service.
        
        Returns:
            ModelsOutput: The response from the service
        """
        response = self._get(endpoint=DaspeakEndpoints.MODELS.value)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            self._handle_error_response(response)
        except Exception as e:
            raise e
        return ModelsOutput(status_code=response.status_code, **response.json())

    def generate_credential(self, data_model: ModelsHashCredentialWavInput) -> ModelsHashCredentialWavOutput:
        """
        Generate a credential from a WAV file.

        **Warning**: if the audio provided is a `BytesIO` object, make sure to close it after using this method.

        Args:
            data_model: The data required to generate the credential

        Returns:
            ModelsHashCredentialWavOutput: The response from the service
        """
        endpoint = DaspeakEndpoints.MODELS_HASH_CREDENTIAL_WAV.value.replace("<hash>", data_model.hash)
        audio = self._get_virtual_audio_file(data_model.audio)
        files = {
            "audio": ("audio", audio.read(), "audio/wav")
        }
        data = {
            "channel": data_model.channel,
            "calibration": data_model.calibration
        }
        response = self._post(endpoint=endpoint, data=data, files=files)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            self._handle_error_response(response)
        return ModelsHashCredentialWavOutput(status_code=response.status_code, **response.json())

    def _get_virtual_audio_file(self, audio_input):
        if isinstance(audio_input, str):
            try:
                audio = open(audio_input, "rb")
            except FileNotFoundError:
                raise FileNotFoundError(f"File {audio_input} not found")
        elif isinstance(audio_input, BytesIO):
            audio = audio_input
        else:
            raise ValueError("audio must be a string or a BytesIO object")
        return audio
