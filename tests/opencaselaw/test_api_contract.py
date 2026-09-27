"""Check wrapper requests against a compact, independently fetched API contract."""

import inspect
import json
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest

from opencaselaw import OpenCaseLawClient

CONTRACT = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "public_api_contract.json").read_text()
)
GET_METHODS = {
    "/lookup": "lookup",
    "/tool": "list_tools",
    "/decisions": "search_decisions",
    "/decisions/{decision_id}": "get_decision",
    "/courts": "list_courts",
    "/integrity/{decision_id}": "get_integrity_proof",
    "/scraper-health": "get_scraper_health",
    "/statistics": "get_statistics",
    "/citations/{decision_id}": "get_citations",
    "/appeal-chain/{decision_id}": "get_appeal_chain",
    "/leading-cases": "find_leading_cases",
    "/trends": "analyze_trends",
    "/laws/search": "search_laws",
    "/laws/{abbreviation}": "get_law",
    "/laws/{abbreviation}/{canton}": "get_cantonal_law",
    "/amendment-ref": "resolve_amendment_ref",
    "/commentaries/search": "search_commentaries",
    "/commentaries/{abbreviation}": "get_commentary",
    "/scholarship/search": "search_scholarship",
    "/scholarship/sources": "list_scholarship_sources",
    "/scholarship/licenses": "get_scholarship_licenses",
    "/scholarship/citation-stats": "get_scholarship_citation_stats",
    "/scholarship/cited-by-statute": "find_scholarship_citing_statute",
    "/scholarship/cited-by-decision": "find_scholarship_citing_decision",
    "/scholarship-fulltext": "get_scholarship_full_text",
    "/scholarship/{pub_id}": "get_scholarship",
    "/materialien/{law_code}": "get_materialien",
    "/materialien": "search_materialien",
    "/legislation/search": "search_legislation",
    "/legislation/changes": "get_legislation_changes",
    "/legislation/{lexfind_id}": "get_legislation",
    "/doctrine": "get_doctrine",
    "/case-brief/{case}": "get_case_brief",
    "/cite": "cite",
    "/decisions/{decision_id}/export.docx": "export_docx",
    "/decisions/{decision_id}/export.pdf": "export_pdf",
    "/decisions/{decision_id}/export.bib": "export_bib",
    "/decisions/{decision_id}/export.ris": "export_ris",
    "/atom/{court}.xml": "atom_feed",
    "/erwaegung/{decision_id}/{e_number}": "get_erwaegung",
    "/relevant-erwaegung/{decision_id}": "find_relevant_erwaegung",
    "/article-purpose/{sr_number}/{article}": "get_article_purpose",
    "/search-botschaft": "search_botschaft",
    "/article-history/{sr_number}/{article}": "get_article_history",
    "/regeste/{decision_id}": "get_regeste",
    "/structure/{decision_id}": "get_structure",
    "/exam-question": "generate_exam_question",
}
GET_OPERATIONS = [op for op in CONTRACT["operations"] if op["method"] == "GET"]


def test_public_get_route_coverage() -> None:
    assert set(GET_METHODS) == {op["path"] for op in GET_OPERATIONS}


@pytest.mark.parametrize("operation", GET_OPERATIONS, ids=lambda op: op["path"])
def test_all_documented_get_parameters_reach_transport(operation: dict) -> None:
    arguments = {}
    expected_query = {}
    expected_path = "/api" + operation["path"]
    for parameter in operation["parameters"]:
        name = parameter["name"]
        if name == "format":
            # JSON is the default; the XML variant has a dedicated wrapper/test.
            continue
        schema = parameter["schema"]
        kind = schema["type"]
        if kind == "boolean":
            value = False
            serialized = "false"
        elif kind in {"integer", "number"}:
            value = schema.get("default", schema.get("minimum", 1))
            serialized = str(value)
        else:
            value = "reference/with space" if parameter["in"] == "path" else name + " value"
            serialized = value
        arguments[name] = value
        if parameter["in"] == "query":
            expected_query[name] = serialized
        else:
            expected_path = expected_path.replace("{" + name + "}", quote(serialized, safe=""))

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"decision_id": "test", "sr_number": "220", "results": []})

    with OpenCaseLawClient(
        base_url="https://example.test/api",
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        method = getattr(client, GET_METHODS[operation["path"]])
        # Optional server parameters must also be optional in the Python wrapper.
        signature = inspect.signature(method)
        for parameter in operation["parameters"]:
            if parameter["name"] != "format" and not parameter["required"]:
                assert (
                    signature.parameters[parameter["name"]].default is not inspect.Parameter.empty
                )
        method(**arguments)
    assert len(seen) == 1
    assert seen[0].method == "GET"
    assert seen[0].url.raw_path.split(b"?")[0] == expected_path.encode()
    assert dict(seen[0].url.params) == expected_query
