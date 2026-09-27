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

    with pytest.raises(ValueError, match="unknown"):
        load_config(config_path)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("base_url", "ftp://example.test/api", "base_url must start with http"),
        ("base_url", "   ", "base_url must not be empty"),
        ("timeout", 0, "greater than 0"),
        (
            "rate_limit_delay",
            -0.1,
            "greater than or equal to 0",
        ),
        ("default_limit", 0, "greater than 0"),
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


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("field", ["timeout", "rate_limit_delay"])
def test_config_rejects_nonfinite_values(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        OpenCaseLawConfig(**{field: value})


@pytest.mark.parametrize(
    "url", ["https:///api", "https://example.test/api?q=x", "https://user:pass@example.test/api"]
)
def test_config_rejects_unsafe_base_urls(url: str) -> None:
    with pytest.raises(ValueError):
        OpenCaseLawConfig(base_url=url)


@pytest.mark.parametrize("content", ["false", "0", "[]", "opencaselaw: []", "1: bad\nother: bad"])
def test_config_rejects_nonmapping_or_nonstring_keys(tmp_path: Path, content: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_config_normalizes_url() -> None:
    assert (
        OpenCaseLawConfig(base_url=" https://example.test/api/ ").base_url
        == "https://example.test/api"
    )


def test_config_validation_error_does_not_display_credentials() -> None:
    with pytest.raises(ValueError) as error:
        OpenCaseLawConfig(base_url="https://user:secret@example.test/api")
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("value", [True, 2.5])
def test_config_rejects_noninteger_limit(value: object) -> None:
    with pytest.raises(ValueError, match="default_limit"):
        OpenCaseLawConfig(default_limit=value)


def test_empty_and_missing_config_use_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    assert load_config(path) == DEFAULT_CONFIG
    path.write_text("", encoding="utf-8")
    assert load_config(path) == DEFAULT_CONFIG


def test_malformed_yaml_has_a_sanitized_error(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("secret: [", encoding="utf-8")
    with pytest.raises(ValueError, match="valid YAML") as error:
        load_config(path)
    assert "secret" not in str(error.value)
