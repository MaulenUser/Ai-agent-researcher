from app.link_extractor import extract_links, normalize_url
from app.taxonomy import candidates, classify, classify_all

BASE = "https://cb.example/docs/index.html"

HTML = b"""
<html><body>
  <nav>
    <a href="/en/research/research-papers">Research papers</a>
    <a href="/en/about/cookie-management">Cookie Guidelines</a>
    <a href="/letoltes/ccyb-methodology-q42024-en.pdf">Applicable from Q4 2024</a>
    <a href="/en/about/museum">Museum</a>
  </nav>
  <h2>Decisions</h2>
  <a href="/decisions/previous">Previous decisions and systemic risk maps</a>
  <a href="/letoltes/ccyb-indoklas-2026q2-en.pdf">24 June 2026</a>
  <a href="/en/financial-stability/related-links">Related links</a>
  <a href="/docs/index.html/?utm_source=x#top">Self</a>
  <a href="mailto:x@y.z">mail</a>
</body></html>
"""


def links_by_anchor():
    return {l["anchor_text"]: l for l in classify_all(extract_links(HTML, BASE))}


def test_normalize_url_drops_fragment_utm_and_trailing_slash():
    assert normalize_url("https://CB.Example/a/b/?utm_source=x&q=1#top") == \
        "https://cb.example/a/b?q=1"


def test_pdf_in_nav_stays_high_value():
    # правило 2 срабатывает раньше правила 5: меню не понижает документ
    link = links_by_anchor()["Applicable from Q4 2024"]

    assert link["in_nav"] == "nav"
    assert link["class"] == "HIGH_VALUE"
    assert link["reason"] == "matched url pattern: methodology + pdf"


def test_research_papers_in_nav_is_not_navigation():
    link = links_by_anchor()["Research papers"]

    assert link["class"] == "POTENTIALLY_RELEVANT"
    assert link["reason"] == "matched anchor: research paper"


def test_cookie_guidelines_is_navigation_despite_guideline_substring():
    link = links_by_anchor()["Cookie Guidelines"]

    assert link["class"] == "NAVIGATION"
    assert link["reason"] == "matched global navigation anchor: Cookie Guidelines"


def test_document_without_topic_signal_is_potentially_relevant():
    link = links_by_anchor()["24 June 2026"]

    assert link["class"] == "POTENTIALLY_RELEVANT"
    assert link["reason"] == "document extension without topic signal: pdf"


def test_navigation_filtering_leaves_candidates():
    all_links = classify_all(extract_links(HTML, BASE))

    assert [l["anchor_text"] for l in candidates(all_links)] == [
        "Research papers",
        "Applicable from Q4 2024",
        "Previous decisions and systemic risk maps",
        "24 June 2026",
        "Related links",
    ]
    museum = links_by_anchor()["Museum"]
    assert museum["class"] == "IRRELEVANT"
    assert museum["reason"] == "matched unrelated topic: museum"


def test_context_captured_for_content_links():
    assert links_by_anchor()["Previous decisions and systemic risk maps"]["context"] == "Decisions"


def test_classify_uses_anchor_and_url_only():
    assert classify({"url": "https://x/y", "anchor_text": "Press release on CCyB"}) == {
        "class": "HIGH_VALUE",
        "reason": "matched high-value anchor: press release",
    }
