import pytest

from opencaselaw.models import (
    Citation,
    Court,
    Decision,
    DecisionSearchResult,
    DecisionSummary,
    Law,
    LawArticle,
)


def test_decision_search_result_parses_results_and_metadata() -> None:
    payload = {
        "total": 2,
        "limit": 1,
        "offset": 0,
        "results": [
            {
                "decision_id": "bge_BGE_140_III_86",
                "court": "bge",
                "decision_date": "2014-04-15",
                "language": "de",
                "title": "Mietrecht",
                "regeste": "Headnote",
                "citation_string_de": "BGE 140 III 86",
                "canonical_url": "https://mcp.opencaselaw.ch/entscheid/x",
                "extra": "kept",
            }
        ],
    }

    result = DecisionSearchResult.from_json(payload)

    assert result.total == 2
    assert result.limit == 1
    assert result.offset == 0
    assert result.results == [
        DecisionSummary(
            decision_id="bge_BGE_140_III_86",
            court="bge",
            decision_date="2014-04-15",
            language="de",
            title="Mietrecht",
            regeste="Headnote",
            citation_string_de="BGE 140 III 86",
            citation_string_fr=None,
            citation_string_it=None,
            canonical_url="https://mcp.opencaselaw.ch/entscheid/x",
            rule_statement=None,
            raw=payload["results"][0],
        )
    ]


def test_decision_parses_common_fields_and_preserves_raw() -> None:
    payload = {
        "decision_id": "bger_4A_747_2012",
        "docket_number": "4A_747/2012",
        "court": "bger",
        "decision_date": "2013-04-15",
        "language": "de",
        "title": "Test decision",
        "full_text": "Full text",
        "canonical_url": "https://example.test/decision",
    }

    decision = Decision.from_json(payload)

    assert decision.decision_id == "bger_4A_747_2012"
    assert decision.docket_number == "4A_747/2012"
    assert decision.full_text == "Full text"
    assert decision.raw is payload


def test_law_parses_articles() -> None:
    payload = {
        "sr_number": "220",
        "abbreviation": "OR",
        "title": "Obligationenrecht",
        "consolidation_date": "2026-01-01",
        "language": "de",
        "articles": [
            {
                "article_num": "41",
                "heading": None,
                "text": "Wer einem andern widerrechtlich Schaden zufügt...",
            }
        ],
    }

    law = Law.from_json(payload)

    assert law.sr_number == "220"
    assert law.abbreviation == "OR"
    assert law.articles == [
        LawArticle(
            article_num="41",
            heading=None,
            text="Wer einem andern widerrechtlich Schaden zufügt...",
            raw=payload["articles"][0],
        )
    ]


def test_court_and_citation_parse_optional_fields() -> None:
    court = Court.from_json({"court": "bger", "name": "Bundesgericht", "count": 10})
    citation = Citation.from_json(
        {
            "decision_id": "bge_BGE_140_III_86",
            "citation_string_de": "BGE 140 III 86",
            "canonical_url": "https://example.test",
            "exists": True,
        }
    )

    assert court.court == "bger"
    assert court.name == "Bundesgericht"
    assert court.count == 10
    assert citation.decision_id == "bge_BGE_140_III_86"
    assert citation.exists is True


@pytest.mark.parametrize(
    ("model", "payload", "message"),
    [
        (DecisionSummary, {}, "decision_id"),
        (Decision, {"decision_id": None}, "decision_id"),
        (LawArticle, {"article_num": "41"}, "text"),
        (Court, {}, "court"),
    ],
)
def test_models_reject_missing_required_strings(
    model: type[DecisionSummary] | type[Decision] | type[LawArticle] | type[Court],
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        model.from_json(payload)


@pytest.mark.parametrize("value", [None, "bad", {}, ["bad"], [{"decision_id": "valid"}, 42]])
def test_search_rejects_malformed_results(value: object) -> None:
    with pytest.raises(ValueError):
        DecisionSearchResult.from_json({"results": value})


@pytest.mark.parametrize("value", [None, "bad", {}, ["bad"]])
def test_law_rejects_malformed_articles(value: object) -> None:
    with pytest.raises(ValueError):
        Law.from_json({"articles": value})


@pytest.mark.parametrize("value", [True, [], {}, " "])
def test_decision_rejects_invalid_identifier(value: object) -> None:
    with pytest.raises(ValueError):
        Decision.from_json({"decision_id": value})


def test_nested_payloads_preserve_unknown_fields_and_identity() -> None:
    item = {"decision_id": "test", "extra": {"source": "example"}}
    payload = {"results": [item], "extra": "kept"}
    result = DecisionSearchResult.from_json(payload)
    assert result.raw is payload
    assert result.results[0].raw is item
    assert result.total == result.limit == 1
    assert result.offset == 0


def test_court_aliases_are_supported() -> None:
    court = Court.from_json({"court_code": "bger", "decision_count": 3})
    assert court.court == "bger"
    assert court.count == 3


@pytest.mark.parametrize("value", [-1, 1.5, True, "bad"])
def test_search_rejects_invalid_counts(value: object) -> None:
    with pytest.raises(ValueError, match="total"):
        DecisionSearchResult.from_json({"total": value})


def test_law_text_is_not_stripped() -> None:
    article = LawArticle.from_json({"article_num": "1", "text": "  Text\n"})
    assert article.text == "  Text\n"


def test_models_validate_direct_construction_and_are_frozen() -> None:
    with pytest.raises(ValueError, match="decision_id"):
        Decision(decision_id={})
    decision = Decision(decision_id="test")
    with pytest.raises(ValueError, match="frozen"):
        decision.decision_id = "changed"
