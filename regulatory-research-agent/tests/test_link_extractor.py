from app.link_extractor import extract_links, normalize_url
from app.taxonomy import candidates, classify_all

BASE = "https://cb.example/docs/index.html"

QUESTION = "What is the current CCyB rate and how is it set?"

PAGE = "Countercyclical capital buffer (CCyB)"

HTML = b"""
<html><body>
  <nav>
    <a href="/en/research/research-papers">Research papers</a>
    <a href="/en/about/cookie-management">Cookie Guidelines</a>
    <a href="/letoltes/ccyb-methodology-q42024-en.pdf">Applicable from Q4 2024</a>
    <a href="/en/about/museum">Museum</a>
  </nav>
  <main>
    <h2>Decisions</h2>
    <a href="/decisions/previous">Previous decisions and systemic risk maps</a>
    <a href="/letoltes/ccyb-indoklas-2026q2-en.pdf">24 June 2026</a>
    <a href="/en/financial-stability/related-links">Related links</a>
    <a href="/docs/index.html/?utm_source=x#top">Self</a>
    <a href="mailto:x@y.z">mail</a>
  </main>
</body></html>
"""


def links_by_anchor():
    return {l["anchor_text"]: l
            for l in classify_all(extract_links(HTML, BASE), QUESTION, PAGE)}


def test_normalize_url_drops_fragment_utm_and_trailing_slash():
    assert normalize_url("https://CB.Example/a/b/?utm_source=x&q=1#top") == \
        "https://cb.example/a/b?q=1"


def test_dom_container_is_nav_for_links_inside_menu():
    assert links_by_anchor()["Research papers"]["context"]["dom_container"] == "nav"


def test_section_heading_and_surrounding_text_are_captured():
    context = links_by_anchor()["Previous decisions and systemic risk maps"]["context"]

    assert context["section_heading"] == "Decisions"
    assert context["dom_container"] == "main"
    assert "Previous decisions" in context["surrounding_text"]


def test_pdf_in_nav_stays_high_value():
    # §6.1: расширение документа блокирует P-3, меню не понижает документ
    assert links_by_anchor()["Applicable from Q4 2024"]["class"] == "HIGH_VALUE"


def test_research_papers_in_nav_is_not_navigation():
    # P-3 не применяется к primary-группам; темы страницы меню не наследует,
    # поэтому primary + topic_match none -> POTENTIALLY_RELEVANT (§6)
    assert links_by_anchor()["Research papers"]["class"] == "POTENTIALLY_RELEVANT"


def test_cookie_guidelines_is_navigation_despite_guideline_anchor():
    assert links_by_anchor()["Cookie Guidelines"]["class"] == "NAVIGATION"


def test_museum_is_irrelevant_by_positive_signal():
    museum = links_by_anchor()["Museum"]

    assert museum["class"] == "IRRELEVANT"
    assert museum["rule"] == "P-2"


def test_navigation_filtering_leaves_candidates():
    all_links = classify_all(extract_links(HTML, BASE), QUESTION, PAGE)

    assert [l["anchor_text"] for l in candidates(all_links)] == [
        "Research papers",
        "Applicable from Q4 2024",
        "Previous decisions and systemic risk maps",
        "24 June 2026",
        "Related links",
        "Self",
    ]


def test_non_http_schemes_are_dropped():
    assert "mail" not in links_by_anchor()
