"""A guard on every client's real-infrastructure coverage.

The mocked tests assert against fabricated responses, so they cannot tell whether a request
is one the service would accept. That is the gap that hid the das-Peak identification field
names (#28) and made the VCSP batch archive format guesswork (#39). Every public method
therefore needs at least one test that runs against the real service.

This checks it mechanically, so a method added later cannot quietly ship with only mocked
coverage. It reads the test sources; it runs nothing.
"""

import inspect
import re
from pathlib import Path

import pytest

from vericlient import DasfaceClient, DaspeakClient, VcspClient

TESTS = Path(__file__).parent

# How a test declares it will not run outside mock mode.
MOCK_ONLY_MARKERS = (
    "skip_if_not_mock",
    'pytest.skip("This test only runs in mock mode")',
    'pytest.skip("These are mocked error bodies")',
    'pytest.skip("This is a mocked error body")',
    'pytest.skip("Covered against the real service by',
)

CLIENTS = [
    (DaspeakClient, "daspeak"),
    (VcspClient, "vcsp"),
    (DasfaceClient, "dasface"),
]


def _source_reaching_the_service(package: str) -> str:
    """Return the test source for one client that actually reaches its service.

    Fixtures count: `temp_subject` enrolling a subject is real coverage of `enroll_subject`.
    """
    directory = TESTS / package
    sources = []
    for path in sorted(directory.glob("*.py")):
        text = path.read_text()
        if path.name == "conftest.py":
            sources.append(text)
            continue
        blocks = re.findall(r"def (test_\w+)\([^)]*\):((?:.|\n)*?)(?=\n@pytest|\Z)", text)
        sources += [body for _, body in blocks if not any(m in body for m in MOCK_ONLY_MARKERS)]
    return "\n".join(sources)


@pytest.mark.parametrize(("client", "package"), CLIENTS, ids=[package for _, package in CLIENTS])
def test_every_public_method_is_exercised_against_real_infrastructure(client, package):
    methods = [name for name, _ in inspect.getmembers(client, inspect.isfunction) if not name.startswith("_")]
    assert methods, f"no public methods found on {client.__name__}, the check would pass vacuously"

    source = _source_reaching_the_service(package)
    missing = sorted(name for name in methods if not re.search(rf"\.{name}\(", source))

    assert not missing, (
        f"these {client.__name__} methods have no test that runs against real infrastructure: "
        f"{missing}. A mocked test cannot tell whether the service would accept the request."
    )
