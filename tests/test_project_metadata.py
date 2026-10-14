import re
import tomllib
from pathlib import Path

import yaml


def test_jupyter_is_not_a_runtime_dependency() -> None:
    metadata = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )

    dependencies = metadata["project"]["dependencies"]
    dev_dependencies = metadata["dependency-groups"]["dev"]

    assert not any(dependency.startswith("jupyter") for dependency in dependencies)
    assert any(dependency.startswith("jupyter") for dependency in dev_dependencies)


def test_ci_covers_supported_versions_and_pins_every_action() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.load((root / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    assert (root / ".python-version").read_text().strip() == "3.13"
    quality_steps = workflow["jobs"]["quality"]["steps"]
    setup = next(step["with"] for step in quality_steps if "setup-uv@" in step.get("uses", ""))
    assert setup["python-version-file"] == ".python-version"
    compatibility_steps = workflow["jobs"]["compatibility"]["steps"]
    setup = next(
        step["with"] for step in compatibility_steps if "setup-uv@" in step.get("uses", "")
    )
    assert setup["python-version"] == "3.14"
    for steps in (quality_steps, compatibility_steps):
        assert any(step.get("run") == "uv run --no-sync pytest -q" for step in steps)

    audit = yaml.load((root / ".github/workflows/security.yml").read_text(), Loader=yaml.BaseLoader)
    assert "schedule" in audit["on"]
    assert {"pyproject.toml", "uv.lock"} <= set(audit["on"]["pull_request"]["paths"])
    assert audit["jobs"]["dependencies"]["steps"][-1]["run"] == (
        "uv audit --locked --preview-features audit-command"
    )
    for path in (root / ".github/workflows").glob("*.yml"):
        config = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        assert config["permissions"] == {"contents": "read"}
        for job in config["jobs"].values():
            for step in job["steps"]:
                if "uses" in step:
                    assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"])


def test_checkout_config_contains_explicit_package_defaults() -> None:
    from opencaselaw import DEFAULT_CONFIG, load_config

    path = Path(__file__).resolve().parents[1] / "config.yaml"
    settings = yaml.safe_load(path.read_text(encoding="utf-8"))["opencaselaw"]
    assert settings == DEFAULT_CONFIG.model_dump()
    assert load_config(path) == DEFAULT_CONFIG
