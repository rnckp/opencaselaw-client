"""Require an explicit opt-in before tests contact the public API."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Expose the read-only live-test switch."""
    parser.addoption("--live-api", action="store_true", help="Run read-only public API smoke tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live requests in the default deterministic suite."""
    if config.getoption("--live-api"):
        return
    skip = pytest.mark.skip(reason="Public API requests require --live-api")
    for item in items:
        if "live_api" in item.keywords:
            item.add_marker(skip)
