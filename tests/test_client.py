import json
from pathlib import Path

import httpx
import pytest

from opencaselaw.client import OpenCaseLawClient
from opencaselaw.models import Citation, Decision, DecisionSearchResult, Law


def _client_with_handler(
    handler: httpx.MockTransport | httpx.BaseTransport,
) -> OpenCaseLawClient:
    return OpenCaseLawClient(
        base_url="https://example.test/api",
        rate_limit_delay=0,
        transport=handler,
    )


def _json_response(data: object) -> httpx.Response:
    return httpx.Response(200, json=data)


def test_search_decisions_builds_query_and_parses_result() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response(
            {
                "total": 1,
                "limit": 5,
                "offset": 10,
                "results": [{"decision_id": "bger_4A_747_2012"}],
            }
        )

    client = _client_with_handler(httpx.MockTransport(handler))

    result = client.search_decisions(
        query="Mietrecht",
        court="bger",
        canton="CH",
        language="de",
        date_from="2010-01-01",
        date_to="2020-01-01",
        chamber="I",
        decision_type="Urteil",
        limit=5,
        offset=10,
        sort="date_desc",
        fields="compact",
    )

    assert isinstance(result, DecisionSearchResult)
    assert result.total == 1
    assert seen_request is not None
    assert seen_request.method == "GET"
    assert seen_request.url.path == "/api/decisions"
    assert seen_request.url.params["query"] == "Mietrecht"
    assert seen_request.url.params["court"] == "bger"
    assert seen_request.url.params["limit"] == "5"
    assert seen_request.url.params["offset"] == "10"
    assert "full_text" not in seen_request.url.params


def test_search_decisions_uses_config_default_limit_when_omitted(
    tmp_path: Path,
) -> None:
    seen_request: httpx.Request | None = None
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
opencaselaw:
  default_limit: 7
""",
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response({"total": 0, "limit": 7, "offset": 0, "results": []})

    client = OpenCaseLawClient(
        base_url="https://example.test/api",
        config_path=config_path,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    )

    client.search_decisions(query="Mietrecht")

    assert seen_request is not None
    assert seen_request.url.params["limit"] == "7"


def test_search_decisions_accepts_request_timeout() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response({"total": 0, "limit": 3, "offset": 0, "results": []})

    client = _client_with_handler(httpx.MockTransport(handler))

    result = client.search_decisions(
        query="Bundesgericht",
        limit=3,
        request_timeout=60.0,
    )

    assert result.total == 0
    assert seen_request is not None
    assert seen_request.url.path == "/api/decisions"
    assert seen_request.extensions["timeout"]["read"] == 60.0


def test_get_decision_quotes_path_segment_and_parses_result() -> None:
    seen_path = ""
    seen_raw_path = b""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_path, seen_raw_path
        seen_path = request.url.path
        seen_raw_path = request.url.raw_path
        return _json_response(
            {
                "decision_id": "bger_4A_747_2012",
                "docket_number": "4A_747/2012",
                "full_text": "Text",
            }
        )

    client = _client_with_handler(httpx.MockTransport(handler))

    decision = client.get_decision("4A_747/2012", full_text=False)

    assert isinstance(decision, Decision)
    assert decision.docket_number == "4A_747/2012"
    assert seen_path == "/api/decisions/4A_747/2012"
    assert seen_raw_path == b"/api/decisions/4A_747%2F2012?full_text=false"


def test_get_law_and_cite_parse_typed_models() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/laws/OR":
            assert request.url.params["article"] == "41"
            return _json_response(
                {
                    "sr_number": "220",
                    "abbreviation": "OR",
                    "title": "Obligationenrecht",
                    "articles": [{"article_num": "41", "text": "Text"}],
                }
            )
        if request.url.path == "/api/cite":
            assert request.url.params["reference"] == "BGE 140 III 86"
            return _json_response(
                {
                    "decision_id": "bge_BGE_140_III_86",
                    "citation_string_de": "BGE 140 III 86",
                    "exists": True,
                }
            )
        raise AssertionError(f"Unexpected path: {request.url.path}")

    client = _client_with_handler(httpx.MockTransport(handler))

    law = client.get_law("OR", article="41")
    citation = client.cite("BGE 140 III 86")

    assert isinstance(law, Law)
    assert law.articles[0].article_num == "41"
    assert isinstance(citation, Citation)
    assert citation.exists is True


def test_list_courts_accepts_array_response() -> None:
    client = _client_with_handler(
        httpx.MockTransport(
            lambda request: _json_response(
                [{"court": "bger", "name": "Bundesgericht", "count": 10}]
            )
        )
    )

    courts = client.list_courts()
    court_models = client.list_court_models()

    assert courts == [{"court": "bger", "name": "Bundesgericht", "count": 10}]
    assert len(court_models) == 1
    assert court_models[0].court == "bger"


def test_export_methods_return_response_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/export.docx"):
            return httpx.Response(200, content=b"docx")
        if request.url.path.endswith("/export.pdf"):
            return httpx.Response(200, content=b"pdf")
        if request.url.path.endswith("/export.bib"):
            return httpx.Response(200, text="@case{test}")
        if request.url.path.endswith("/export.ris"):
            return httpx.Response(200, text="TY  - CASE")
        raise AssertionError(f"Unexpected path: {request.url.path}")

    client = _client_with_handler(httpx.MockTransport(handler))

    assert client.export_docx("bger_4A_747_2012") == b"docx"
    assert client.export_pdf("bger_4A_747_2012") == b"pdf"
    assert client.export_bib("bger_4A_747_2012") == "@case{test}"
    assert client.export_ris("bger_4A_747_2012") == "TY  - CASE"


def test_mock_decision_accepts_request_timeout() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response({"ok": True})

    client = _client_with_handler(httpx.MockTransport(handler))

    assert client.mock_decision("facts", request_timeout=120.0) == {"ok": True}
    assert seen_request is not None
    assert seen_request.url.path == "/api/mock-decision"
    assert seen_request.extensions["timeout"]["read"] == 120.0


@pytest.mark.parametrize(
    ("method_name", "args", "kwargs", "expected_method", "expected_path"),
    [
        ("list_courts", (), {}, "GET", "/api/courts"),
        (
            "get_statistics",
            (),
            {"court": "bger", "year": 2024},
            "GET",
            "/api/statistics",
        ),
        ("get_scraper_health", (), {}, "GET", "/api/scraper-health"),
        ("get_integrity_proof", ("bger_1",), {}, "GET", "/api/integrity/bger_1"),
        ("get_citations", ("bger_1",), {}, "GET", "/api/citations/bger_1"),
        ("get_appeal_chain", ("bger_1",), {}, "GET", "/api/appeal-chain/bger_1"),
        ("find_leading_cases", (), {"query": "Miete"}, "GET", "/api/leading-cases"),
        ("analyze_trends", (), {"query": "Miete"}, "GET", "/api/trends"),
        ("search_laws", ("Kündigung",), {}, "GET", "/api/laws/search"),
        ("resolve_amendment_ref", ("AS", 2020, 1), {}, "GET", "/api/amendment-ref"),
        ("search_commentaries", ("Art. 41 OR",), {}, "GET", "/api/commentaries/search"),
        ("get_commentary", ("OR",), {"article": "41"}, "GET", "/api/commentaries/OR"),
        ("search_materialien", ("Haftung",), {}, "GET", "/api/materialien"),
        ("get_materialien", ("OR",), {"article": "41"}, "GET", "/api/materialien/OR"),
        ("search_legislation", ("Datenschutz",), {}, "GET", "/api/legislation/search"),
        ("get_legislation", (123,), {}, "GET", "/api/legislation/123"),
        (
            "get_legislation_changes",
            (),
            {"canton": "ZH"},
            "GET",
            "/api/legislation/changes",
        ),
        ("get_doctrine", ("Art. 41 OR",), {}, "GET", "/api/doctrine"),
        (
            "get_case_brief",
            ("BGE 140 III 86",),
            {},
            "GET",
            "/api/case-brief/BGE%20140%20III%2086",
        ),
        ("attest", ("BGE 140 III 86",), {}, "POST", "/api/attest"),
        ("verify_claim", ("claim", "bger_1"), {}, "POST", "/api/verify-claim"),
        ("mock_decision", ("facts",), {}, "POST", "/api/mock-decision"),
        ("get_regeste", ("bger_1",), {}, "GET", "/api/regeste/bger_1"),
        ("get_structure", ("bger_1",), {}, "GET", "/api/structure/bger_1"),
        ("get_erwaegung", ("bger_1", "2.3"), {}, "GET", "/api/erwaegung/bger_1/2.3"),
        (
            "find_relevant_erwaegung",
            ("bger_1", "claim"),
            {},
            "GET",
            "/api/relevant-erwaegung/bger_1",
        ),
        (
            "get_article_purpose",
            ("220", "41"),
            {},
            "GET",
            "/api/article-purpose/220/41",
        ),
        ("search_botschaft", ("Haftung",), {}, "GET", "/api/search-botschaft"),
        (
            "get_article_history",
            ("220", "41"),
            {},
            "GET",
            "/api/article-history/220/41",
        ),
        ("generate_exam_question", ("Vertragsrecht",), {}, "GET", "/api/exam-question"),
    ],
)
def test_public_json_wrappers(
    method_name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    expected_method: str,
    expected_path: str,
) -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        if request.method == "POST":
            json.loads(request.content.decode("utf-8"))
        return _json_response({"ok": True})

    client = _client_with_handler(httpx.MockTransport(handler))
    method = getattr(client, method_name)

    assert method(*args, **kwargs) == {"ok": True}
    assert seen_requests[0].method == expected_method
    if "%" in expected_path:
        assert seen_requests[0].url.raw_path.split(b"?")[0] == expected_path.encode()
    else:
        assert seen_requests[0].url.path == expected_path


def test_atom_feed_returns_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/atom/bger.xml"
        return httpx.Response(200, text="<feed />")

    client = _client_with_handler(httpx.MockTransport(handler))

    assert client.atom_feed("bger") == "<feed />"


def test_context_manager_closes_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"ok": True})

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.get_statistics() == {"ok": True}

    with pytest.raises(RuntimeError, match="Cannot send a request"):
        client.get_statistics()
