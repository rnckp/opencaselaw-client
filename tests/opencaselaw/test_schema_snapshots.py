"""Validate request and response contracts against vendored upstream schemas."""

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from opencaselaw import Citation, OpenCaseLawAPIError, OpenCaseLawClient

FIXTURES = Path(__file__).parents[1] / "fixtures"
APPLICATION = json.loads((FIXTURES / "application_openapi.json").read_text(encoding="utf-8"))
RESEARCH = json.loads((FIXTURES / "research_openapi.json").read_text(encoding="utf-8"))
RESPONSES = json.loads((FIXTURES / "api_responses.json").read_text(encoding="utf-8"))


def test_schema_snapshots_match_their_recorded_hashes() -> None:
    manifest = json.loads((FIXTURES / "schema_manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["schemas"].values():
        assert (
            hashlib.sha256((FIXTURES / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
        )


def test_saved_request_contract_matches_vendored_application_schema() -> None:
    contract = json.loads((FIXTURES / "public_api_contract.json").read_text(encoding="utf-8"))
    for operation in contract["operations"]:
        actual = APPLICATION["paths"][operation["path"]][operation["method"].lower()]
        parameters = {(p["in"], p["name"]): p for p in actual.get("parameters", [])}
        assert set(parameters) == {(p["in"], p["name"]) for p in operation["parameters"]}
        for saved in operation["parameters"]:
            live = parameters[(saved["in"], saved["name"])]
            assert live.get("required", False) == saved["required"]
            assert {key: live["schema"].get(key) for key in saved["schema"]} == saved["schema"]


@pytest.mark.parametrize(
    "method,path,arguments",
    [
        (
            "mock_decision",
            "/mock-decision",
            {
                "facts": "Non-confidential hypothetical facts",
                "question": "A research question",
                "deciding_court": "bger",
                "preferred_language": "de",
                "statute_references": [{"law": "OR", "article": "41"}],
                "clarifications": [{"question": "Which court?", "answer": "bger"}],
                "fedlex_urls": ["https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de"],
                "limit": 3,
            },
        ),
        (
            "attest",
            "/attest",
            {
                "redacted_text": "BGE 140 III 86",
                "draft_text": "BGE 140 III 86",
                "audit_grounding": False,
                "audit_quotes": True,
                "client_redactor_version": "example",
                "client_redactor_summary": {"removed": 0},
            },
        ),
        (
            "verify_claim",
            "/verify-claim",
            {
                "claim": "A hypothetical claim",
                "decision_id": "bge_BGE_140_III_86",
                "pinpoint": "2",
            },
        ),
    ],
)
def test_post_body_fields_and_types_match_upstream_schema(
    method: str, path: str, arguments: dict[str, Any]
) -> None:
    ref = APPLICATION["paths"][path]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    schema = APPLICATION["components"]["schemas"][ref.rsplit("/", 1)[-1]]
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.method == "POST"
        assert request.url.path == "/api" + path
        body = json.loads(request.content)
        assert body == arguments
        assert set(body) == set(schema["properties"])
        assert set(schema.get("required", [])) <= set(body)
        types = {"string": str, "boolean": bool, "integer": int, "array": list, "object": dict}
        for name, value in body.items():
            assert type(value) is types[schema["properties"][name]["type"]]
        return httpx.Response(200, json={"ok": True})

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        assert getattr(client, method)(**arguments) == {"ok": True}
    assert len(seen) == 1


def test_citation_fixture_preserves_live_invalid_passage_status() -> None:
    result = Citation.from_json(RESPONSES["citation_invalid_pinpoint"])
    assert result.exists is True
    assert result.pinpoint_valid is False
    assert result.pinpoint_status == "invalid"
    assert result.citation_string_de == "BGE 140 III 86"
    assert "UNPINPOINTED" in result.pinpoint_note


def test_live_law_error_fixture_is_not_an_empty_success() -> None:
    payload = RESPONSES["cantonal_law_error"]
    with OpenCaseLawClient(
        rate_limit_delay=0,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    ) as client:
        with pytest.raises(OpenCaseLawAPIError) as error:
            client.get_cantonal_law("StG", "ZH", article="12")
    assert error.value.payload == payload


def test_typed_research_response_fields_remain_available() -> None:
    from opencaselaw import Decision, DecisionSearchResult, DecisionSummary, Law, LawArticle

    for schema_name, model in [
        ("DecisionRecord", DecisionSummary),
        ("DecisionResponse", Decision),
        ("SearchDecisionsResponse", DecisionSearchResult),
        ("LawResponse", Law),
        ("LawArticle", LawArticle),
        ("CiteResponse", Citation),
    ]:
        schema = RESEARCH["components"]["schemas"][schema_name]
        payload = {
            "decision_id": "public-test-id",
            "sr_number": "220",
            "article_num": "41",
            "exists": False,
            "results": [],
        }
        assert set(schema.get("required", [])) <= set(model.model_fields)
        # Additional upstream fields must survive parsing even before they are typed.
        payload["future_metadata"] = {"status": "example"}
        assert model.from_json(payload).raw["future_metadata"] == {"status": "example"}
