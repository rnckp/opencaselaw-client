"""Read-only deployment smoke tests, enabled explicitly with --live-api."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from opencaselaw import OpenCaseLawAPIError, OpenCaseLawClient

pytestmark = pytest.mark.live_api
FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.fixture(scope="module")
def live_client() -> Iterator[OpenCaseLawClient]:
    """Use public defaults, ignoring local configuration and pacing requests."""
    with OpenCaseLawClient(timeout=60, rate_limit_delay=0.25, auto_discover_config=False) as client:
        yield client


def test_live_request_contract_has_not_drifted(live_client: OpenCaseLawClient) -> None:
    schema = live_client.get_openapi()
    snapshot = json.loads((FIXTURES / "application_openapi.json").read_text(encoding="utf-8"))
    contract = json.loads((FIXTURES / "public_api_contract.json").read_text(encoding="utf-8"))
    for operation in contract["operations"]:
        actual = schema["paths"][operation["path"]][operation["method"].lower()]
        actual_parameters = {(p["in"], p["name"]): p for p in actual.get("parameters", [])}
        assert set(actual_parameters) == {(p["in"], p["name"]) for p in operation["parameters"]}
        for saved in operation["parameters"]:
            live = actual_parameters[(saved["in"], saved["name"])]
            assert live.get("required", False) == saved["required"]
            assert {key: live["schema"].get(key) for key in saved["schema"]} == saved["schema"]
    for path in ["/mock-decision", "/attest", "/verify-claim"]:
        ref = snapshot["paths"][path]["post"]["requestBody"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        live_ref = schema["paths"][path]["post"]["requestBody"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        expected_body = snapshot["components"]["schemas"][ref.rsplit("/", 1)[-1]]
        live_body = schema["components"]["schemas"][live_ref.rsplit("/", 1)[-1]]
        assert set(live_body["properties"]) == set(expected_body["properties"])
        assert set(live_body.get("required", [])) == set(expected_body.get("required", []))
        for name, expected in expected_body["properties"].items():
            actual = live_body["properties"][name]
            for constraint in ["type", "nullable", "default", "minimum", "maximum", "items"]:
                assert actual.get(constraint) == expected.get(constraint)
    research = live_client.get_openapi(research=True)
    assert "/decisions" in research["paths"]


def test_live_core_research_responses_are_populated(live_client: OpenCaseLawClient) -> None:
    assert live_client.list_court_models()
    search = live_client.search_decisions(query="Mietrecht", limit=1, include_pinpoint=False)
    assert len(search.results) == 1
    assert search.returned == 1
    assert search.has_more is not None
    assert live_client.get_decision(search.results[0].decision_id, full_text=False).decision_id
    law = live_client.get_law("OR", article="41", language="de")
    assert law.sr_number == "220"
    assert law.articles and law.articles[0].article_num == "41"
    assert law.articles[0].text


def test_live_slash_reference_resolves(live_client: OpenCaseLawClient) -> None:
    assert (
        live_client.get_decision("4A_747/2012", full_text=False).decision_id == "bger_4A_747_2012"
    )


def test_live_invalid_pinpoint_is_not_validated(live_client: OpenCaseLawClient) -> None:
    citation = live_client.cite("BGE 140 III 86", pinpoint="999999")
    assert citation.exists is True
    assert citation.pinpoint_valid is False
    assert citation.pinpoint_status == "invalid"
    assert citation.pinpoint_note


def test_live_cantonal_failure_is_explicit(live_client: OpenCaseLawClient) -> None:
    with pytest.raises(OpenCaseLawAPIError) as error:
        live_client.get_cantonal_law("__opencaselaw_nonexistent_law__", "ZH", article="12")
    assert error.value.payload["error"]


def test_live_publication_filters(live_client: OpenCaseLawClient) -> None:
    result = live_client.search_decisions(
        court="bger",
        published_from="2026-01-01",
        published_to="2026-10-23",
        sort="published_desc",
        include_pinpoint=False,
        limit=2,
    )
    assert result.results
    dates = [decision.publication_date for decision in result.results]
    assert all(date is not None and "2026-01-01" <= date <= "2026-10-23" for date in dates)
    assert dates == sorted(dates, reverse=True)


def test_live_material_document_types(live_client: OpenCaseLawClient) -> None:
    search = live_client.search_botschaft(q="Haftung", doc_type="botschaft", limit=1)
    assert search["doc_type_filter"] == "botschaft"
    assert search["results"]
    assert all(hit["doc_type"] == "botschaft" for hit in search["results"])
    materials = live_client.get_materialien("OR", article="41", doc_type="botschaft")
    assert materials["doc_type_filter"] == "botschaft"
    assert all(hit["doc_type"] == "botschaft" for hit in materials["botschaft_documents"])
    digest = live_client.search_materialien(q="Haftung", doc_type="botschaft", limit=1)
    assert digest["doc_type_filter"] == "botschaft"
    assert digest["doc_type_note"]


@pytest.mark.parametrize(
    "method,arguments",
    [
        ("get_statistics", {}),
        ("get_scraper_health", {}),
        ("list_tools", {}),
        ("get_citations", {"decision_id": "bge_BGE_140_III_86", "limit": 1}),
        ("get_appeal_chain", {"decision_id": "bge_BGE_140_III_86"}),
        ("get_structure", {"decision_id": "bge_BGE_140_III_86"}),
        ("get_regeste", {"decision_id": "bge_BGE_140_III_86"}),
        ("search_laws", {"q": "Haftung", "limit": 1}),
        ("search_legislation", {"q": "Obligationenrecht", "limit": 1}),
        ("search_commentaries", {"q": "Haftung", "limit": 1}),
        ("search_scholarship", {"q": "Mietrecht", "limit": 1}),
        ("list_scholarship_sources", {}),
        ("get_scholarship_licenses", {}),
        ("get_scholarship_citation_stats", {}),
    ],
)
def test_live_public_read_endpoints(
    live_client: OpenCaseLawClient, method: str, arguments: dict
) -> None:
    assert getattr(live_client, method)(**arguments)
