"""Building the archive that batch enrolment expects.

VCSP takes batch enrolments as a TAR archive holding the biometric samples and an
`applicants.json` describing them. Neither the file name nor the way an entry points at its
sample is written down anywhere: both were found by reading the errors the service returns.
The sample reference is a URI, and `file://` is the only scheme it accepts.
"""

import io
import json
import os
import tarfile

APPLICANTS_FILE = "applicants.json"
SAMPLE_SCHEME = "file://"


def build_batch_archive(entries: list[tuple[str, bytes, dict]]) -> bytes:
    """Build the TAR archive for a batch enrolment.

    Args:
        entries: One tuple per enrolment, holding the sample's name inside the archive, the
            sample itself, and the applicant as a dictionary

    Returns:
        The archive, ready to be posted as `batch_file`

    """
    applicants = [{"sample": f"{SAMPLE_SCHEME}{filename}", "applicant": applicant} for filename, _, applicant in entries]
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        for filename, sample, _ in entries:
            _add(tar, filename, sample)
        _add(tar, APPLICANTS_FILE, json.dumps(applicants).encode())
    return archive.getvalue()


def _add(tar: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(payload)
    tar.addfile(info, io.BytesIO(payload))


def sample_filename(sample: str | bytes, index: int, given: str | None) -> str:
    """Return the name a sample takes inside the archive.

    Uses the name the caller gave, then the file name when the sample is a path, and finally
    a generated one. Only has to be unique within the archive.
    """
    if given:
        return given
    if isinstance(sample, str):
        return os.path.basename(sample)
    return f"sample_{index}"
