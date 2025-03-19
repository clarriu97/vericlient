"""Fixtures for VCSP tests."""
import pytest

from vericlient import VcspClient


@pytest.fixture
def vcsp_client(mock_server, test_environment, all_environments) -> VcspClient:
    """Create a VCSP client for testing.

    This fixture creates a client that can be used for all VCSP tests.
    """
    if mock_server:
        return VcspClient()

    if test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")

    env_mapping = {
        "EU_SANDBOX": ("SANDBOX", "EU"),
        "EU_PRODUCTION": ("PRODUCTION", "EU"),
        "US_SANDBOX": ("SANDBOX", "US"),
        "US_PRODUCTION": ("PRODUCTION", "US"),
    }

    environment, location = env_mapping.get(test_environment)

    return VcspClient(
        environment=environment,
        location=location,
    )
