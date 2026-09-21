"""A guard on the VCSP client's real-infrastructure coverage.

The mocked tests assert against fabricated responses, so they cannot tell whether a request
is one the service would accept — that is what caught the identification field names in #28
and the batch archive format in #39. Every public method therefore needs at least one test
that runs against real infrastructure.

This checks that mechanically, so a method added later does not quietly ship with only mocked
coverage. It reads the test sources rather than running anything.
"""

import inspect
import re
from pathlib import Path

from vericlient import VcspClient

HERE = Path(__file__).parent

# How a test declares it will not run outside mock mode.
MOCK_ONLY_MARKERS = (
    "skip_if_not_mock",
    'pytest.skip("This test only runs in mock mode")',
)


def _source_that_runs_against_real_infrastructure() -> str:
    """Return the test source that actually reaches the service.

    Fixtures count: `temp_subject` enrolling a subject is real coverage of `enroll_subject`.
    """
    tests = (HERE / "test_vcsp.py").read_text()
    blocks = re.findall(r"def (test_\w+)\([^)]*\):((?:.|\n)*?)(?=\n@pytest|\Z)", tests)
    real = [body for _, body in blocks if not any(marker in body for marker in MOCK_ONLY_MARKERS)]
    return "\n".join(real) + (HERE / "conftest.py").read_text()


def test_every_public_client_method_is_exercised_against_real_infrastructure():
    methods = [name for name, _ in inspect.getmembers(VcspClient, inspect.isfunction) if not name.startswith("_")]
    assert methods, "no public methods found, the check would pass vacuously"

    source = _source_that_runs_against_real_infrastructure()
    missing = sorted(name for name in methods if not re.search(rf"\.{name}\(", source))

    assert not missing, (
        "these VcspClient methods have no test that runs against real infrastructure: "
        f"{missing}. A mocked test cannot tell whether the service would accept the request."
    )
