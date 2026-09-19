"""Share credentials, read from the environment.

Held as a Pydantic model so the password is a `SecretStr` and cannot reach a
log line by accident, and so a partially configured share is a distinguishable
state rather than a connection that fails for no stated reason.
"""

from collections.abc import Sequence

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from smbfence.errors import ShareConfigError

MISSING_CREDENTIALS = (
    "Share is not configured: SMB_HOST, SMB_SHARE, SMB_USER and SMB_PASSWORD must all be set"
)


class ShareConfig(BaseSettings):
    """What is needed to reach one share."""

    model_config = SettingsConfigDict(env_prefix="SMB_", env_file="secrets.env", extra="ignore")

    host: str = ""
    share: str = ""
    user: str = ""
    password: SecretStr = SecretStr("")
    port: int = 445
    allowed_paths: Sequence[str] = Field(default=())

    @property
    def is_configured(self) -> bool:
        """Whether there are credentials for the share at all.

        Distinct from reachability: this answers "should anything be attempted",
        which a caller often needs before it has a connection to ask.
        """
        return bool(self.host and self.share and self.user and self.password.get_secret_value())

    def require(self) -> None:
        """Raise `ShareConfigError` unless every credential is present."""
        if not self.is_configured:
            raise ShareConfigError(MISSING_CREDENTIALS)
