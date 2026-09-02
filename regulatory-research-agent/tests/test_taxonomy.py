"""Regression-тесты классификации: фиксируют разбор известных ссылок MNB."""

import pytest

from app.taxonomy import candidates, classify, is_ignored, matches_keyword

TOPIC = {"countercyclical", "capital", "buffer", "ccyb"}


def cls(anchor: str, url: str, in_nav: str | None = None, topic: set[str] = TOPIC) -> dict:
    return classify(
        {"url": url, "anchor_text": anchor, "in_nav": in_nav},
        topic,
    )


# --- совпадение по границам токенов, а не по подстроке ---

@pytest.mark.parametrize("text, keyword", [
    ("Resolution on the CCyB rate", "resolution"),
    ("https://www.mnb.hu/en/resolution/", "resolution"),
    ("https://www.mnb.hu/en/resolution", "resolution"),
    ("resolution-of-the-board", "resolution"),
    ("Previous decisions and justifications", "decision"),      # множественное число
    ("/publications/reports/", "report"),
    ("Methodologies applied until Q1 2024", "methodology"),
    ("Cookie Guidelines", "guideline"),
    ("Press release on the review", "press release"),
    ("press-releases-2026", "press release"),
])
def test_matches_keyword(text, keyword):
    assert matches_keyword(text, keyword)


@pytest.mark.parametrize("text, keyword", [
    ("mind", "ind"),
    ("https://www.mnb.hu/web/en/mind", "ind"),
    ("Information for data suppliers", "report"),               # reporting != report
    ("https://aszp.mnb.hu/mnb-data-reporting", "report"),
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
    assert cls("2015/1", "https://www.esrb.europa.eu/pub/pdf/recommendations/")["class"] != \
        "POTENTIALLY_RELEVANT"


# --- шум не должен попадать в crawl candidates ---

@pytest.mark.parametrize("anchor, url", [
    ("Cookie Guidelines", "https://www.mnb.hu/en/the-central-bank/cookie-management-at-mnb-hu"),
    ("Contact Us", "https://www.mnb.hu/en/contact"),
    ("Careers", "https://www.mnb.hu/en/career/vacancies"),
    ("Sitemap", "https://www.mnb.hu/en/sitemap"),
    ("Search", "https://www.mnb.hu/en/search"),
    ("Museum", "https://www.mnb.hu/en/the-central-bank/museum"),
    ("Payment Systems Report", "https://www.mnb.hu/en/publications/reports/payment-systems-report"),
    ("Publications", "https://www.mnb.hu/en/publications"),
])
def test_noise_is_not_a_candidate(anchor, url):
    result = cls(anchor, url, in_nav="nav")

    assert result["class"] in {"NAVIGATION", "IRRELEVANT", "OTHER"}
    assert result["reason"]
    assert not candidates([result | {"anchor_text": anchor}])


def test_cookie_guidelines_is_navigation():
    assert cls("Cookie Guidelines", "https://www.mnb.hu/en/cookie-management") == {
        "class": "NAVIGATION",
        "reason": "matched global navigation anchor: Cookie Guidelines",
    }


# --- известные релевантные материалы не теряются ---

def test_ccyb_methodology_pdf_is_high_value():
    assert cls("CCyB methodology", "https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf") == {
        "class": "HIGH_VALUE",
        "reason": "matched high-value anchor: methodology",
    }


def test_methodology_pdf_in_menu_survives_navigation_filter():
    """Документ в меню не понижается до NAVIGATION (link-taxonomy.md §6.1)."""
    result = cls("Applicable from Q4 2024",
                 "https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf",
                 in_nav="nav")

    assert result == {"class": "HIGH_VALUE", "reason": "matched url pattern: methodology + pdf"}


@pytest.mark.parametrize("anchor, url, expected", [
    ("Press release on the review of the CCyB rate (30 June 2026)",
     "https://www.mnb.hu/en/pressroom/press-releases/press-releases-2026/the-mnb-maintains",
     "HIGH_VALUE"),
    ("Previous decisions, justifications and systemic risk maps",
     "https://www.mnb.hu/en/financial-stability/macroprudential-policy/the-macroprudential-"
     "toolkit/countercyclical-capital-buffer-ccyb/previous-decisions-and-justifications",
     "HIGH_VALUE"),
    ("Macroprudential report",
     "https://www.mnb.hu/en/financial-stability/macroprudential-policy/macroprudential-report",
     "HIGH_VALUE"),
    ("24 June 2026", "https://www.mnb.hu/letoltes/ccyb-indoklas-2026q2-en.pdf",
     "POTENTIALLY_RELEVANT"),
    ("Link", "https://www.mnb.hu/letoltes/ccyb-data-adatok-2026q2.xlsx", "POTENTIALLY_RELEVANT"),
    ("Related links", "https://www.mnb.hu/en/financial-stability/related-links",
     "POTENTIALLY_RELEVANT"),
    ("Research papers", "https://www.mnb.hu/en/financial-stability/publications/research-papers",
     "POTENTIALLY_RELEVANT"),
])
def test_known_materials_stay_candidates(anchor, url, expected):
    # in_nav="nav": боковое меню раздела не должно их терять
    assert cls(anchor, url, in_nav="nav")["class"] == expected


def test_research_paper_is_not_globally_navigation():
    """Тот же anchor вне меню тоже остаётся кандидатом — класс не зависит от списка навигации."""
    assert cls("Research paper on CCyB", "https://x/research/paper")["class"] == "POTENTIALLY_RELEVANT"


# --- прочее ---

def test_every_link_gets_class_and_reason():
    result = cls("Something entirely unknown", "https://www.mnb.hu/en/whatever")

    assert set(result) == {"class", "reason"}
    assert result["class"] == "OTHER"
    assert result["reason"] == "no rule matched"


def test_p0_ignores_assets():
    assert is_ignored("https://www.mnb.hu/static/logo.svg")
    assert not is_ignored("https://www.mnb.hu/letoltes/ccyb-methodology-q42024-en.pdf")
