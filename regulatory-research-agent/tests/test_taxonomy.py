"""Regression-тесты классификации на реальных ссылках MNB.

Соответствие спецификации проверяет test_taxonomy_spec.py (evaluation dataset
link-taxonomy.md §12). Здесь фиксируется, что на живой странице CCyB известные
материалы не теряются, а шум не попадает в кандидаты.
"""

import pytest

from app.taxonomy import classify, is_ignored, matches_keyword, normalize_question

QUESTION = "What is the current CCyB rate and how is it set?"

PAGE = "Countercyclical capital buffer (CCyB)"


def cls(anchor: str, url: str, container: str = "main", heading: str = "",
        question: str = QUESTION) -> dict:
    return classify(
        {
            "url": url,
            "anchor_text": anchor,
            "same_domain": True,
            "context": {"dom_container": container, "section_heading": heading,
                        "surrounding_text": ""},
        },
        question,
        PAGE,
    )


# --- совпадение по границам токенов, а не по подстроке ---

@pytest.mark.parametrize("text, keyword", [
    ("Resolution on the CCyB rate", "resolution"),
    ("https://www.mnb.hu/en/resolution/", "resolution"),
    ("resolution-of-the-board", "resolution"),
    ("Previous decisions and justifications", "decision"),      # множественное число
    ("/publications/reports/", "report"),
    ("Methodologies applied until Q1 2024", "methodology"),
    ("Press release on the review", "press release"),
    ("press-releases-2026", "press release"),
])
def test_matches_keyword(text, keyword):
    assert matches_keyword(text, keyword)


@pytest.mark.parametrize("text, keyword", [
    ("mind", "ind"),
    ("Information for data suppliers", "report"),               # reporting != report
    ("Research papers", "search"),                              # research != search
    ("irresolution", "resolution"),
    ("opinionated", "opinion"),
    ("/pdf/recommendations/", "decision"),
])
def test_does_not_match_substring_inside_word(text, keyword):
    assert not matches_keyword(text, keyword)


def test_pdf_segment_in_url_is_not_a_document_extension():
    # .../pub/pdf/recommendations/ESRB_2015_1.en.pdf — документ, а
    # .../pub/pdf/recommendations/ — раздел, а не файл
    from app.taxonomy import _extension

    assert _extension("/pub/pdf/recommendations/") is None
    assert _extension("/pub/pdf/recommendations/esrb_2015_1.en.pdf") == "pdf"


# --- §3: расширение вопроса синонимами ---

def test_question_expands_via_synonyms():
    terms = normalize_question(QUESTION)

    assert "countercyclical capital buffer" in terms      # synonyms: ccyb
    assert "the" not in terms                             # stopwords


# --- шум не должен попадать в crawl candidates ---

@pytest.mark.parametrize("anchor, url, expected", [
    ("Cookie Guidelines", "https://www.mnb.hu/en/the-central-bank/cookie-management-at-mnb-hu",
     "NAVIGATION"),
    ("Contact Us", "https://www.mnb.hu/en/contact", "NAVIGATION"),
    ("Careers", "https://www.mnb.hu/en/career/vacancies", "NAVIGATION"),
    ("Sitemap", "https://www.mnb.hu/en/sitemap", "NAVIGATION"),
    ("Search", "https://www.mnb.hu/en/search", "NAVIGATION"),
    ("Museum", "https://www.mnb.hu/en/the-central-bank/museum", "IRRELEVANT"),
    ("Payment Systems Report", "https://www.mnb.hu/en/publications/reports/payment-systems-report",
     "IRRELEVANT"),
    ("Publications", "https://www.mnb.hu/en/publications", "NAVIGATION"),
])
def test_noise_is_not_a_candidate(anchor, url, expected):
    result = cls(anchor, url, container="nav")

    assert result["class"] == expected
    assert result["rule"] and result["reason"]


def test_cookie_guidelines_is_navigation_outside_menu():
    """Навигационный признак в URL сильнее слабого `guidelines` в anchor."""
    assert cls("Cookie Guidelines", "https://www.mnb.hu/en/cookie-management")["class"] == \
        "NAVIGATION"


# --- известные релевантные материалы не теряются ---

@pytest.mark.parametrize("anchor, url", [
    ("CCyB methodology", "https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf"),
    # обобщённый anchor: группа берётся из URL (P-4)
    ("Applicable from Q4 2024", "https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf"),
    ("Press release on the review of the CCyB rate (30 June 2026)",
     "https://www.mnb.hu/en/pressroom/press-releases/press-releases-2026/the-mnb-maintains"),
    ("Previous decisions, justifications and systemic risk maps",
     "https://www.mnb.hu/en/financial-stability/macroprudential-policy/the-macroprudential-"
     "toolkit/countercyclical-capital-buffer-ccyb/previous-decisions-and-justifications"),
    ("Macroprudential report",
     "https://www.mnb.hu/en/financial-stability/macroprudential-policy/macroprudential-report"),
    ("Link", "https://www.mnb.hu/letoltes/ccyb-data-adatok-2026q2.xlsx"),
    ("Research papers", "https://www.mnb.hu/en/financial-stability/publications/research-papers"),
])
def test_known_materials_are_high_value_even_in_menu(anchor, url):
    # container="nav": боковое меню раздела не должно их терять
    assert cls(anchor, url, container="nav")["class"] == "HIGH_VALUE"


@pytest.mark.parametrize("anchor, url", [
    # дата вместо anchor: группы нет, но тема в URL есть -> кандидат, не HIGH_VALUE
    ("24 June 2026", "https://www.mnb.hu/letoltes/ccyb-indoklas-2026q2-en.pdf"),
    ("Related links", "https://www.mnb.hu/en/financial-stability/related-links"),
])
def test_known_materials_stay_candidates(anchor, url):
    assert cls(anchor, url, container="nav")["class"] == "POTENTIALLY_RELEVANT"


def test_document_in_menu_is_never_navigation():
    """§6.1: pdf блокирует P-3 даже в подвале."""
    result = cls("Download", "https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf",
                 container="footer")

    assert result["class"] == "HIGH_VALUE"


# --- зависимость от research_question (§12, критерий 2) ---

def test_class_depends_on_research_question():
    url = "https://www.mnb.hu/en/monetary-policy"

    assert cls("Monetary policy", url)["class"] == "IRRELEVANT"
    assert cls("Monetary policy", url,
               question="How does monetary policy interact with the CCyB?")["class"] != "IRRELEVANT"


# --- прочее ---

def test_unrecognised_link_is_unknown_not_irrelevant():
    """IRRELEVANT — положительно определяемый класс, а не остаток (§1)."""
    result = cls("Something entirely unknown", "https://www.mnb.hu/en/whatever")

    # тема страницы-источника даёт partial: ссылка без группы остаётся кандидатом
    assert result["class"] == "POTENTIALLY_RELEVANT"
    assert set(result) == {"class", "rule", "reason"}

    # без темы вообще — UNKNOWN, а не IRRELEVANT (§1: IRRELEVANT не остаток)
    unknown = classify(
        {"url": "https://www.mnb.hu/en/whatever", "anchor_text": "Something entirely unknown"},
        QUESTION,
    )

    assert unknown["class"] == "UNKNOWN"


def test_p0_ignores_assets_and_schemes():
    assert is_ignored("https://www.mnb.hu/static/logo.svg")
    assert is_ignored("mailto:info@mnb.hu")
    assert not is_ignored("https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf")
