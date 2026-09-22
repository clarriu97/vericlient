"""Some general utility functions for the VeriClient."""

import base64

DEFAULT_CONTENT_TYPE = "application/octet-stream"

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def get_virtual_file(input_file: object) -> bytes:
    """Get the content of a file as bytes. The input can be a path to a file or a bytes object.

    Args:
        input_file: The file to read the content from
    Returns:
        The content of the file as bytes

    """
    if isinstance(input_file, str):
        try:
            with open(input_file, "rb") as f:
                sample = f.read()
        except FileNotFoundError as e:
            error = f"File {input_file} not found"
            raise FileNotFoundError(error) from e
    elif isinstance(input_file, bytes):
        sample = input_file
    else:
        error = "sample must be a string or a bytes object"
        raise TypeError(error)
    return sample


def guess_content_type(sample: bytes) -> str:
    """Guess the media type of an in-memory sample from its leading bytes.

    A path can be handed to `mimetypes`, but a bytes object carries no filename, so its
    magic bytes are all there is to go on. This matters because VCSP answers with a 500
    when the declared media type does not match the content it receives.

    Args:
        sample: The sample content

    Returns:
        The guessed media type, or `application/octet-stream` when it is not recognised

    """
    if sample[:3] == _JPEG_MAGIC:
        return "image/jpeg"
    if sample[:8] == _PNG_MAGIC:
        return "image/png"
    if sample[:4] == b"RIFF" and sample[8:12] == b"WAVE":
        return "audio/wav"
    if sample[4:8] == b"ftyp":
        return "video/mp4"
    return DEFAULT_CONTENT_TYPE


def encode_base64(input_file: object) -> str:
    """Read a file or a bytes object and return it base64 encoded.

    das-Face takes its images inside a JSON body rather than as multipart parts, so every
    image has to be encoded before it is sent.

    Args:
        input_file: A path to a file, or its content as bytes

    Returns:
        The content, base64 encoded, as ASCII text

    """
    return base64.b64encode(get_virtual_file(input_file)).decode("ascii")
