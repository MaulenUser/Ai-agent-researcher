"""Evaluation dataset link-taxonomy.md §12 — проверка соответствия спецификации.

Тесты этого файла проверяют не поведение реализации, а критерии приёмки §12:
20/20 ожидаемых классов, зависимость от research_question, отсутствие
остаточного IRRELEVANT, доля UNKNOWN <= 10 %.
"""

import json
from pathlib import Path

import pytest

from app.taxonomy import classify

CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "link_classification_cases.json").read_text("utf-8")
)


def to_link(case: dict) -> dict:
    """`surrounding_context` фикстуры -> Link.context (link-taxonomy.md §2.1).

    Формат фикстуры: "<контейнер> / <заголовок или описание блока>",
    где заголовок помечен префиксом `section:` или `heading:`.
    """
    container, _, rest = case["surrounding_context"].partition(" / ")

    kind, sep, text = rest.partition(":")
    heading = text.strip() if sep and kind in {"section", "heading"} else ""

    return {
        "url": case["target_url"],
        "anchor_text": case["anchor_text"],
        "same_domain": False,
        "context": {
            "dom_container": container.strip(),
            "section_heading": heading,
            "surrounding_text": "" if heading else rest,
        },
    }


def run(case: dict) -> dict:
    return classify(to_link(case), case["research_question"], case["source_page_topic"])


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_expected_class(case):
    """§12, критерий 1."""
    result = run(case)

    assert result["class"] == case["expected_class"], f"{result} / ожидалось {case}"


def test_question_dependency():
    """§12, критерий 2: LC-14 и LC-15 отличаются только research_question."""
    lc14, lc15 = (next(c for c in CASES if c["id"] == i) for i in ("LC-14", "LC-15"))

    assert lc14["target_url"] == lc15["target_url"]
    assert lc14["anchor_text"] == lc15["anchor_text"]
    assert run(lc14)["class"] != run(lc15)["class"]


def test_irrelevant_is_never_a_leftover():
    """§12, критерий 3: у каждого IRRELEVANT есть идентификатор правила."""
    for case in CASES:
        result = run(case)

        if result["class"] == "IRRELEVANT":
            assert result["rule"] in {"P-1", "P-2", "P-5", "P-6"}, result

            # единственный путь к IRRELEVANT через матрицу — группа unrelated_topic
            assert result["rule"] != "P-6" or "unrelated_topic" in result["reason"], result


def test_unknown_share_within_threshold():
    """§12, критерий 4: доля UNKNOWN <= 10 %."""
    unknown = [c["id"] for c in CASES if run(c)["class"] == "UNKNOWN"]

    assert len(unknown) <= len(CASES) // 10, unknown


def test_classification_is_deterministic():
    """§7: один и тот же вход даёт один и тот же выход."""
    assert [run(c) for c in CASES] == [run(c) for c in CASES]
