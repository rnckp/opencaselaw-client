import tomllib
from pathlib import Path


def test_jupyter_is_not_a_runtime_dependency() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = metadata["project"]["dependencies"]
    dev_dependencies = metadata["dependency-groups"]["dev"]

    assert not any(dependency.startswith("jupyter") for dependency in dependencies)
    assert any(dependency.startswith("jupyter") for dependency in dev_dependencies)
