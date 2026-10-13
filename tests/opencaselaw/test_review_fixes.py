"""Regression contracts for the October API review findings."""

from pathlib import Path

import httpx
import pytest

import opencaselaw
from opencaselaw import DEFAULT_CONFIG, Citation, OpenCaseLawClient, load_config


def test_invalid_pinpoint_is_exposed_without_hiding_reference_success() -> None:
    citation = Citation.from_json(
        {
            "exists": True,
            "pinpoint": "2.3",
            "pinpoint_status": "invalid",
            "pinpoint_valid": False,
            "pinpoint_note": "The returned citation has no pinpoint.",
            "valid_pinpoints": ["2", "3"],
        }
    )
    assert citation.exists is True
    assert citation.pinpoint_valid is False
    assert citation.pinpoint_status == "invalid"
    assert citation.pinpoint == "2.3"
    assert citation.valid_pinpoints == ["2", "3"]
    assert citation.pinpoint_note == "The returned citation has no pinpoint."


def test_slash_docket_resolves_exactly_before_fetching() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/api/lookup":
            assert dict(request.url.params) == {"q": "4A_747/2012", "exact": "true", "limit": "25"}
            return httpx.Response(
                200, json={"total": 1, "results": [{"decision_id": "bger_4A_747_2012"}]}
            )
        assert request.url.path == "/api/decisions/bger_4A_747_2012"
        assert request.url.params["full_text"] == "false"
        return httpx.Response(200, json={"decision_id": "bger_4A_747_2012"})

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.get_decision("4A_747/2012", full_text=False).decision_id == "bger_4A_747_2012"
    assert paths == ["/api/lookup", "/api/decisions/bger_4A_747_2012"]


@pytest.mark.parametrize(
    "payload",
    [
        {"total": 0, "results": []},
        {"total": 2, "results": [{"decision_id": "one"}, {"decision_id": "two"}]},
        {"total": 1, "partial": True, "results": [{"decision_id": "one"}]},
        {"total": 1, "partial": "true", "results": [{"decision_id": "one"}]},
        {"total": 1, "exact": False, "results": [{"decision_id": "one"}]},
        {"total": True, "results": [{"decision_id": "one"}]},
        {"total": 25, "results": [{"decision_id": "one"}]},
        {"total": 1, "results": [{"decision_id": "still/has/slashes"}]},
    ],
)
def test_unresolved_docket_never_fetches_an_arbitrary_decision(payload: dict) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        assert request.url.path == "/api/lookup"
        return httpx.Response(200, json=payload)

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="resolve"):
            client.get_decision("4A_747/2012")
    assert seen == ["/api/lookup"]


@pytest.mark.parametrize(
    "method,args",
    [
        ("get_cantonal_law", ("StG", "ZH")),
        ("get_law", ("StG",)),
        ("search_decisions", ("test",)),
        ("cite", ("test",)),
        ("verify_claim", ("test", "id")),
        ("list_courts", ()),
    ],
)
def test_http_success_application_errors_raise_with_payload(method: str, args: tuple) -> None:
    payload = {"error": "Lookup failed", "candidates": []}
    with OpenCaseLawClient(
        rate_limit_delay=0,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    ) as client:
        with pytest.raises(opencaselaw.OpenCaseLawAPIError) as error:
            getattr(client, method)(*args)
    assert error.value.payload == payload
    assert "Lookup failed" not in str(error.value)


def test_completed_miss_and_empty_search_remain_successful() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"exists": False}
            if request.url.path.endswith("cite")
            else {"total": 0, "results": [], "error": None},
        )

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.cite("missing").exists is False
        assert client.search_decisions("missing").results == []


def test_unrelated_automatic_config_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("application:\n  port: 8000\n", encoding="utf-8")
    assert load_config() == DEFAULT_CONFIG
    with OpenCaseLawClient(base_url="https://example.test/api") as client:
        assert client.base_url == "https://example.test/api"
    with pytest.raises(ValueError):
        load_config(tmp_path / "config.yaml")


def test_automatic_config_discovery_can_be_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("opencaselaw:\n  timeout: 99\n", encoding="utf-8")
    with OpenCaseLawClient(auto_discover_config=False) as client:
        assert client.timeout == DEFAULT_CONFIG.timeout
    with OpenCaseLawClient(
        config_path=tmp_path / "config.yaml", auto_discover_config=False
    ) as client:
        assert client.timeout == 99
