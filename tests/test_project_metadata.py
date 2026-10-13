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
    assert {"3.13", "3.14"} <= set(workflow["jobs"]["quality"]["strategy"]["matrix"]["python"])
    assert workflow["permissions"] == {"contents": "read"}
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"])
    review = workflow["jobs"]["dependency-review"]
    assert review["if"] == "github.event_name == 'pull_request'"
    assert review["steps"][-1]["with"]["fail-on-severity"] == "high"


def test_checkout_config_contains_explicit_package_defaults() -> None:
    from opencaselaw import DEFAULT_CONFIG, load_config

    path = Path(__file__).resolve().parents[1] / "config.yaml"
    settings = yaml.safe_load(path.read_text(encoding="utf-8"))["opencaselaw"]
    assert settings == DEFAULT_CONFIG.model_dump()
    assert load_config(path) == DEFAULT_CONFIG
