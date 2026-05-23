# OpenCaseLaw Python Client

**Independent Python client for accessing the public no-key [OpenCaseLaw](https://opencaselaw.ch) REST API more easily.**

This project is not official, associated with, or affiliated with OpenCaseLaw. It was developed independently as a convenience wrapper around the publicly documented OpenCaseLaw API.

**Note:** The official [OpenCaseLaw website](https://opencaselaw.ch) and [API documentation](https://opencaselaw.ch/api) are the actual and authoritative reference for the API.

## Installation

```bash
uv sync
```

## Quick Start

For a broader tour of the public API, see [examples/opencaselaw_demo.ipynb](examples/opencaselaw_demo.ipynb).

```python
from opencaselaw import OpenCaseLawClient

with OpenCaseLawClient() as client:
    # Search for court decisions
    results = client.search_decisions(
        query="Mietrecht Kündigung",
        court="bger",
        language="de",
        limit=5,
    )

    for decision in results.results:
        print(decision.citation_string_de, decision.canonical_url)

    # Fetch a decision
    decision = client.get_decision("bger_4A_747_2012")
    print(decision.title)

    # Look up a statute article
    law = client.get_law("OR", article="41", language="de")
    print(law.articles[0].text)

    # Build a canonical citation
    citation = client.cite("BGE 140 III 86", pinpoint="2.3")
    print(citation.citation_string_de)
```

## API Reference

### Decisions

```python
results = client.search_decisions(
    query="Arbeitsvertrag Kündigung",
    court="bger",             # court code, e.g. "bger", "bvger"
    canton="CH",              # "CH", "ZH", "BE", ...
    language="de",            # "de", "fr", "it", "rm"
    date_from="2020-01-01",
    date_to="2024-12-31",
    chamber="I",              # optional chamber substring
    decision_type="Urteil",
    limit=20,
    offset=0,
    sort="date_desc",         # "relevance", "date_desc", "date_asc"
    fields="compact",         # "full" or "compact"
    request_timeout=60.0,      # optional per-call timeout for slow broad searches
)

decision = client.get_decision("bger_4A_747_2012", full_text=True)
```

`search_decisions()` returns a `DecisionSearchResult` with `DecisionSummary` items. `get_decision()` returns a `Decision`.

### Courts, Statistics, and Health

```python
courts = client.list_courts()
statistics = client.get_statistics(court="bger", canton="CH", year=2024)
health = client.get_scraper_health()
integrity = client.get_integrity_proof("bger_4A_747_2012")
```

`list_courts()` returns the raw public API response, which may be a top-level array. Use `list_court_models()` for parsed `Court` items.

### Citation Graph and Citation Integrity

```python
citation = client.cite("BGE 140 III 86", pinpoint="2.3", language="de")
citations = client.get_citations(
    "bger_4A_747_2012",
    direction="both",         # "both", "outgoing", "incoming"
    min_confidence=0.3,
    limit=50,
)
appeal_chain = client.get_appeal_chain("bger_4A_747_2012")
leading = client.find_leading_cases(query="Mietrecht Kündigung", court="bger", limit=10)
trends = client.analyze_trends(query="Datenschutz", court="bger")
```

Audit and claim verification endpoints:

```python
attestation = client.attest(
    draft_text="Gemäss BGE 140 III 86 E. 2.3 gilt ...",
    audit_grounding=False,
    audit_quotes=False,
)

claim_check = client.verify_claim(
    claim="Die Kündigung eines Mietvertrags darf nicht rechtsmissbräuchlich sein.",
    decision_id="bger_4A_747_2012",
    pinpoint="2.3",
)
```

Do not send confidential or personal data to public API endpoints.

### Decision Structure

```python
regeste = client.get_regeste("bger_4A_747_2012")
structure = client.get_structure("bger_4A_747_2012", paragraph_excerpt_chars=500)
erwaegung = client.get_erwaegung("bger_4A_747_2012", "2.3")
relevant = client.find_relevant_erwaegung(
    "bger_4A_747_2012",
    claim="The decision supports this legal proposition.",
    max_paragraphs=5,
)
```

### Statutes

```python
law = client.get_law("OR", article="41", language="de")
search_hits = client.search_laws(
    query="Schadenersatz",
    sr_number="220",
    canton="CH",
    jurisdiction="federal",   # "all", "federal", "cantonal"
    language="de",
    limit=10,
)
amendment = client.resolve_amendment_ref(ref_type="BBl", year=2020, page=1)
```

`get_law()` returns a `Law` with `LawArticle` items. `search_laws()` and `resolve_amendment_ref()` return raw dictionaries because the public OpenAPI response schemas are not fully typed.

### Legislation

```python
legislation_hits = client.search_legislation(
    query="Datenschutz",
    canton="CH",
    language="de",
    limit=20,
    active_only=True,
    search_in_content=False,
    fetch_top_n_texts=0,
)
legislation = client.get_legislation(
    12345,
    systematic_number=None,
    canton="CH",
    language="de",
    include_versions=False,
)
changes = client.get_legislation_changes(canton="CH", language="de")
```

### Commentaries, Doctrine, and Materials

```python
commentary_hits = client.search_commentaries(
    query="Schadenersatz",
    abbreviation="OR",
    language="de",
    limit=10,
)
commentary = client.get_commentary("OR", article="41", language="de")
doctrine = client.get_doctrine("Art. 41 OR Schadenersatz")

materials = client.search_materialien(query="Haftung", law_code="OR", limit=10)
article_materials = client.get_materialien("OR", article="41")
purpose = client.get_article_purpose("220", "41", language="de", max_paragraphs=8)
botschaft = client.search_botschaft("Schadenersatz", language="de", limit=20)
history = client.get_article_history("220", "41", language="de")
```

### Research Helpers

```python
brief = client.get_case_brief("BGE 140 III 86")
exam = client.generate_exam_question("Vertragsrecht")
mock = client.mock_decision(
    facts="Eine Mieterin kündigt nach einer strittigen Nebenkostenabrechnung fristlos.",
    question="Welche zivilrechtlichen Fragen stellen sich?",
    preferred_language="de",
    limit=5,
    request_timeout=120.0,
)
```

`mock_decision()` is a slower research helper. It sends the provided facts and question to the public API and is not legal advice.

### Exports and Feeds

```python
from pathlib import Path

docx = client.export_docx("bger_4A_747_2012")
pdf = client.export_pdf("bger_4A_747_2012")
bib = client.export_bib("bger_4A_747_2012")
ris = client.export_ris("bger_4A_747_2012")
feed = client.atom_feed("bger")

Path("decision.docx").write_bytes(docx)
Path("decision.pdf").write_bytes(pdf)
Path("decision.bib").write_text(bib, encoding="utf-8")
Path("decision.ris").write_text(ris, encoding="utf-8")
```

### Configuration

Runtime defaults are loaded from `config.yaml` when present. Constructor arguments such as `base_url`, `timeout`, and `rate_limit_delay` override configured defaults. Search helpers use `default_limit` when their `limit` argument is omitted.

```yaml
opencaselaw:
  base_url: "https://mcp.opencaselaw.ch/api"
  timeout: 30.0
  rate_limit_delay: 0.2
  default_limit: 10
```

```python
client = OpenCaseLawClient(timeout=10.0, rate_limit_delay=0.5)
```

The default `rate_limit_delay` is `0.2` seconds, matching the public guidance of at most five requests per second per IP.

### Typed Models

```python
from opencaselaw import (
    Citation,
    Court,
    Decision,
    DecisionSearchResult,
    DecisionSummary,
    Law,
    LawArticle,
)
```

The client models stable high-use shapes and preserves unknown fields in each model's `raw` attribute. Endpoints whose response schemas are not fully typed in the OpenAPI document return `dict[str, object]`-style dictionaries.

## Scope

This package covers the public no-key routes documented on the OpenCaseLaw API page. License, payment, and private/admin routes that may appear in the raw OpenAPI schema are intentionally out of scope.

Covered endpoint groups:

- Decisions, courts, statistics, scraper health, and integrity proofs
- Citation graph, appeal chains, leading cases, trends, citation building, attestation, and claim verification
- Decision structure, Regeste, Erwägungen, and relevant Erwägungen
- Laws, legislation, commentaries, doctrine, materials, article purpose, Botschaft search, and article history
- Case briefs, exam questions, mock decisions, exports, and Atom feeds

## Data Sources

OpenCaseLaw describes its public API as covering Swiss court decisions, statutes, commentaries, and citation graph data. The [public documentation](https://opencaselaw.ch/api/) currently references federal, cantonal, regulatory, statute, legislation, commentary, doctrine, materials, and export endpoints.

For coverage details, use:

```python
courts = client.list_courts()
statistics = client.get_statistics()
health = client.get_scraper_health()
```

## Fair Use

This independent client accesses public OpenCaseLaw endpoints.

> [!IMPORTANT]
> Please be kind to the server, keep rate limiting enabled for batch work, mention OpenCaseLaw as the data source when appropriate, and avoid sending confidential or personal data to public endpoints. **Also consider contributing or donating to [OpenCaseLaw](https://opencaselaw.ch/).**

## Development

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest -v
```

## License

This Python client is licensed under the MIT License.

The MIT License applies only to this client code. It does not apply to OpenCaseLaw data, API content, court decisions, statutes, commentaries, or other source materials returned by the service. For data and content licensing details, consult [OpenCaseLaw](https://opencaselaw.ch) and the respective original data sources.
