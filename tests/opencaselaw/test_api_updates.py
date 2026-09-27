"""Regression cases derived from the deployed September 2026 API contracts."""

import json

import httpx
import pytest

from opencaselaw import Law, OpenCaseLawClient
from opencaselaw.models import DecisionSearchResult


@pytest.mark.parametrize(
    ("method", "arguments", "path", "params"),
    [
        (
            "search_decisions",
            {"q": "Miete", "marked_for_publication": True, "include_pinpoint": False},
            "/decisions",
            {
                "q": "Miete",
                "marked_for_publication": "true",
                "include_pinpoint": "false",
                "limit": "10",
                "offset": "0",
            },
        ),
        (
            "get_citations",
            {"decision_id": "test", "offset": 50},
            "/citations/test",
            {"offset": "50", "limit": "10"},
        ),
        (
            "find_leading_cases",
            {"query": "Miete", "include_pinpoint": False},
            "/leading-cases",
            {"query": "Miete", "include_pinpoint": "false", "limit": "10"},
        ),
        (
            "get_commentary",
            {"abbreviation": "VRG", "canton": "SH"},
            "/commentaries/VRG",
            {"canton": "SH"},
        ),
        (
            "search_botschaft",
            {"q": "Haftung", "year_min": 2000, "year_max": 2026},
            "/search-botschaft",
            {"q": "Haftung", "year_min": "2000", "year_max": "2026", "limit": "10"},
        ),
        (
            "lookup",
            {"q": "BGE 140 III 86", "exact": True, "limit": 5},
            "/lookup",
            {"q": "BGE 140 III 86", "exact": "true", "limit": "5"},
        ),
        (
            "search_scholarship",
            {
                "query": "Miete",
                "source": "sui_generis",
                "pub_type": "article",
                "language": "de",
                "year_min": 2020,
                "year_max": 2026,
                "author": "Test",
                "sort": "year",
                "limit": 3,
            },
            "/scholarship/search",
            {
                "query": "Miete",
                "source": "sui_generis",
                "pub_type": "article",
                "language": "de",
                "year_min": "2020",
                "year_max": "2026",
                "author": "Test",
                "sort": "year",
                "limit": "3",
            },
        ),
        ("list_scholarship_sources", {}, "/scholarship/sources", {}),
        ("get_scholarship_licenses", {}, "/scholarship/licenses", {}),
        ("get_scholarship_citation_stats", {}, "/scholarship/citation-stats", {}),
        (
            "find_scholarship_citing_statute",
            {"sr_number": "220", "article": "41", "limit": 4},
            "/scholarship/cited-by-statute",
            {"sr_number": "220", "article": "41", "limit": "4"},
        ),
        (
            "find_scholarship_citing_decision",
            {"decision_id": "test", "limit": 4},
            "/scholarship/cited-by-decision",
            {"decision_id": "test", "limit": "4"},
        ),
        (
            "get_scholarship",
            {"pub_id": "doi:10.1/example"},
            "/scholarship/doi%3A10.1%2Fexample",
            {},
        ),
        (
            "get_scholarship_full_text",
            {"pub_id": "doi:10.1/example"},
            "/scholarship-fulltext",
            {"pub_id": "doi:10.1/example"},
        ),
        ("list_tools", {}, "/tool", {}),
        ("get_openapi", {}, "/openapi.json", {}),
        ("get_openapi", {"research": True}, "/research/openapi.json", {}),
    ],
)
def test_current_query_parameters(method: str, arguments: dict, path: str, params: dict) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"results": []})

    with OpenCaseLawClient(
        base_url="https://example.test/api",
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        getattr(client, method)(**arguments)
    assert len(seen) == 1
    assert seen[0].method == "GET"
    assert seen[0].url.raw_path.split(b"?")[0] == f"/api{path}".encode()
    assert dict(seen[0].url.params) == params


@pytest.mark.parametrize(
    "method",
    [
        "search_laws",
        "search_commentaries",
        "search_materialien",
        "search_legislation",
        "search_botschaft",
        "search_scholarship",
    ],
)
def test_search_q_alias(method: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "Haftung"
        assert "query" not in request.url.params
        return httpx.Response(200, json={})

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        getattr(client, method)(q="Haftung")


@pytest.mark.parametrize("arguments", [{"top_k": 2}, {"max_paragraphs": 2}])
def test_relevant_erwaegung_sends_top_k(arguments: dict) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"claim": "A claim", "top_k": "2"}
        assert request.extensions["timeout"]["read"] == 120.0
        return httpx.Response(200, json={"matches": []})

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        client.find_relevant_erwaegung("test", "A claim", request_timeout=120.0, **arguments)


def test_conflicting_erwaegung_aliases_and_obsolete_filter_do_not_send_requests() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid options must not send an unfiltered request")

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="top_k"):
            client.find_relevant_erwaegung("test", "claim", max_paragraphs=2, top_k=3)
        with pytest.raises(ValueError, match="decision_type"):
            client.search_decisions(decision_type="Urteil")


def test_tool_arguments_are_a_json_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/tool/search_practice"
        assert json.loads(request.content) == {"query": "Mehrwertsteuer", "limit": 2}
        assert not request.url.query
        assert request.extensions["timeout"]["read"] == 120.0
        return httpx.Response(200, json={"results": []})

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.call_tool(
            "search_practice", {"query": "Mehrwertsteuer", "limit": 2}, request_timeout=120.0
        ) == {"results": []}


def test_tool_error_is_not_reported_as_success() -> None:
    from opencaselaw import OpenCaseLawToolError

    payload = {"_is_error": True, "error": "Tool could not complete"}
    with OpenCaseLawClient(
        rate_limit_delay=0,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    ) as client:
        with pytest.raises(OpenCaseLawToolError) as error:
            client.call_tool("search_practice", {})
    assert error.value.payload == payload


def test_cantonal_law_and_xml_use_the_documented_routes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/laws/StG/ZH":
            assert dict(request.url.params) == {"article": "12", "language": "de"}
            return httpx.Response(200, json={"sr_number": "631.1", "canton": "ZH"})
        assert request.url.path == "/api/laws/OR"
        assert dict(request.url.params) == {"article": "41", "format": "xml", "language": "de"}
        return httpx.Response(
            200, text="<akomaNtoso />", headers={"content-type": "application/xml"}
        )

    with OpenCaseLawClient(rate_limit_delay=0, transport=httpx.MockTransport(handler)) as client:
        assert client.get_cantonal_law("StG", "ZH", article="12", language="de").canton == "ZH"
        assert client.get_law_xml("OR", article="41", language="de") == "<akomaNtoso />"


def test_search_metadata_preserves_uncertainty_and_server_continuation() -> None:
    result = DecisionSearchResult.from_json(
        {
            "total": 125,
            "total_is_lower_bound": True,
            "results": [{"decision_id": "test"}],
            "returned": 1,
            "limit": 3,
            "offset": 0,
            "has_more": True,
            "next_offset": 1,
            "degraded": True,
            "note": "Time budget reached",
        }
    )
    assert result.total_is_lower_bound is True
    assert result.returned == 1
    assert result.has_more is True
    assert result.next_offset == 1
    assert result.degraded is True
    assert result.note == "Time budget reached"
    legacy = DecisionSearchResult.from_json({"results": []})
    assert legacy.total_is_lower_bound is None
    assert legacy.has_more is None


def test_law_accepts_documented_table_of_contents_and_empty_text() -> None:
    law = Law.from_json(
        {
            "sr_number": "220",
            "articles": [
                {"article_num": "1", "heading": "Title"},
                {"article_num": "2", "text": "", "text_status": "empty"},
            ],
        }
    )
    assert law.articles[0].text is None
    assert law.articles[1].text == ""
    assert law.articles[1].text_status == "empty"
    assert Law.from_json({"sr_number": "220", "articles": None}).articles is None
