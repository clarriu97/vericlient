"""Some general utility functions for the VeriClient."""


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
