from pathlib import Path

import pytest

from opencaselaw.config import DEFAULT_CONFIG, OpenCaseLawConfig, load_config


def test_default_config_uses_public_api_defaults() -> None:
    assert DEFAULT_CONFIG == OpenCaseLawConfig()
    assert DEFAULT_CONFIG.base_url == "https://mcp.opencaselaw.ch/api"
    assert DEFAULT_CONFIG.timeout == 30.0
    assert DEFAULT_CONFIG.rate_limit_delay == 0.2
    assert DEFAULT_CONFIG.default_limit == 10


def test_load_config_reads_opencaselaw_section(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
opencaselaw:
  base_url: "https://example.test/api"
  timeout: 5
  rate_limit_delay: 0
  default_limit: 25
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.base_url == "https://example.test/api"
    assert config.timeout == 5.0
    assert config.rate_limit_delay == 0.0
    assert config.default_limit == 25


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
opencaselaw:
  unknown: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown config keys: unknown"):
        load_config(config_path)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("base_url", "ftp://example.test/api", "base_url must start with http"),
        ("base_url", "   ", "base_url must not be empty"),
        ("timeout", 0, "timeout must be greater than 0"),
        (
            "rate_limit_delay",
            -0.1,
            "rate_limit_delay must be greater than or equal to 0",
        ),
        ("default_limit", 0, "default_limit must be greater than 0"),
    ],
)
def test_load_config_rejects_invalid_values(
    tmp_path: Path,
    key: str,
    value: object,
    message: str,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
opencaselaw:
  {key}: {value!r}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_config(config_path)
