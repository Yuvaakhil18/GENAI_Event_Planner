"""Runtime configuration, read from environment variables only."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_MODEL = "claude-haiku-5-5"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration loaded from environment variables."""
    # repr=False keeps the key out of logs and tracebacks.
    anthropic_api_key: str | None = field(default=None, repr=False)
    model: str = DEFAULT_MODEL
    request_timeout: float = 15.0

    @classmethod
    def from_env(cls) -> Settings:
        """Create a Settings instance from environment variables."""
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
            model=os.environ.get("PLANNER_MODEL", DEFAULT_MODEL),
            request_timeout=float(os.environ.get("PLANNER_TIMEOUT_SECONDS", "15")),
        )
