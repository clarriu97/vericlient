"""Module to define the exceptions for the Daspeak API."""
from vericlient.exceptions import VeriClientError


class DaspeakError(VeriClientError):
    """Base class for exceptions in the Daspeak API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AudioInputError(DaspeakError):
    """Exception raised for errors in the audio input."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TooManyAudioChannelsError(AudioInputError):
    """Exception raised for too many audio channels."""

    def __init__(self) -> None:
        message = "The maximum allowed number of audio channels is 2, and the audio provided has more channels"
        super().__init__(message)


class UnsupportedSampleRateError(AudioInputError):
    """Exception raised for unsupported sample rates."""

    def __init__(self) -> None:
        message = "The sample rate of the audio is not supported, must be 8 Khz or 16 Khz"
        super().__init__(message)


class AudioDurationTooLongError(AudioInputError):
    """Exception raised for audio duration too long."""

    def __init__(self) -> None:
        message = "The audio duration is too long, must be less than 30 seconds"
        super().__init__(message)


class UnsupportedAudioCodecError(AudioInputError):
    """Exception raised for unsupported audio codec."""

    def __init__(self) -> None:
        message = "The audio codec is not supported. Supported codecs are: 'PCM_16', 'ULAW', 'ALAW'"
        super().__init__(message)


class SignalNoiseRatioError(DaspeakError):
    """Exception raised for errors in the signal noise ratio."""

    def __init__(self) -> None:
        message = "Noise level of the audio exceeded"
        super().__init__(message)


class NetSpeechDurationIsNotEnoughError(DaspeakError):
    """Exception raised for errors in the net speech duration."""

    def __init__(self, net_speech_detected: float) -> None:
        message = (
            f"You need at least 3 seconds of speech to perform the operation, "
            f"but only {net_speech_detected} seconds were detected"
        )
        super().__init__(message)


class InvalidSpecifiedChannelError(DaspeakError):
    """Exception raised for invalid specified channel."""

    def __init__(self) -> None:
        message = "The specified channel is invalid, must be 1 or 2"
        super().__init__(message)


class InsufficientQualityError(DaspeakError):
    """Exception raised for insufficient quality."""

    def __init__(self) -> None:
        message = "The audio quality is insufficient or may contain more than one speaker"
        super().__init__(message)


class CalibrationNotAvailableError(DaspeakError):
    """Exception raised for calibration not available."""

    def __init__(self, calibration: str) -> None:
        message = f"The calibration {calibration} is not available"
        super().__init__(message)
