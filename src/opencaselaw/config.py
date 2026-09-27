"""Validated configuration loading for OpenCaseLaw client defaults."""

from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

PositiveTimeout = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class OpenCaseLawConfig(BaseModel):
    """Runtime settings loaded from config.yaml when available."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    base_url: str = "https://mcp.opencaselaw.ch/api"
    timeout: PositiveTimeout = 30.0
    rate_limit_delay: float = Field(default=0.2, ge=0, allow_inf_nan=False)
    default_limit: int = Field(default=10, gt=0, strict=True)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value:
            raise ValueError("base_url must not be empty")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("base_url must start with http or https")
        if not parsed.hostname or any(character.isspace() for character in value):
            raise ValueError("base_url must have a valid host and no whitespace")
        # Accessing port also validates its syntax and range.
        _ = parsed.port
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("base_url must not contain credentials")
        if "?" in value or "#" in value:
            raise ValueError("base_url must not contain a query or fragment")
        return value


DEFAULT_CONFIG = OpenCaseLawConfig()


def load_config(config_path: Path | str | None = None) -> OpenCaseLawConfig:
    """Load runtime settings from YAML, optionally under ``opencaselaw``.

    Missing files and empty documents use package defaults.

    Raises:
        ValueError: The document or configuration values are invalid.
        OSError: The file exists but cannot be read.
    """
    path = Path(config_path) if config_path is not None else Path("config.yaml")
    if not path.exists():
        return DEFAULT_CONFIG

    try:
        with path.open(encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file)
    except yaml.YAMLError:
        # Parser errors can include complete lines containing sensitive settings.
        raise ValueError("Config file must contain valid YAML") from None

    if raw_config is None:
        return DEFAULT_CONFIG
    if not isinstance(raw_config, dict):
        raise ValueError("Config file must contain a mapping")
    section = raw_config.get("opencaselaw", raw_config)
    if not isinstance(section, dict):
        raise ValueError("The 'opencaselaw' config section must be a mapping")
    return OpenCaseLawConfig.model_validate(section)
