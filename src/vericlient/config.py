"""Configuration the client reads from the environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_TIMEOUT = 10


class Settings(BaseSettings):
    """Values read from the `VERICLIENT_` environment variables.

    Every field is optional, and the client resolves each one in the same order: an
    explicit constructor argument first, then the environment, then its own default. The
    settings object is built per client, so a process can hold two clients pointed at
    different services without one leaking into the other.

    Attributes:
        apikey: The API key to use against the Veridas cloud
        environment: `sandbox` or `production`
        location: `eu` or `us`
        url: A self-hosted URL, which takes the place of the cloud entirely
        timeout: The request timeout in seconds

    """

    model_config = SettingsConfigDict(env_prefix="VERICLIENT_", extra="ignore")

    apikey: str | None = None
    environment: str | None = None
    location: str | None = None
    url: str | None = None
    timeout: int | None = None
