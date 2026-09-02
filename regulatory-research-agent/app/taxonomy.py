"""Классификация ссылок по правилам config/link_taxonomy.yaml.

Порядок правил зафиксирован и не переставляется:

P-0. ссылка не классифицируется вовсе (картинки, стили, скрипты)
P-2/P-5. чужая тема в URL/anchor            → IRRELEVANT
1. explicit HIGH_VALUE      — anchor из high_value
2. explicit document type   — тип документа в URL (+ расширение файла)
3. relevant PDF/document    — расширение .pdf/.xlsx/.docx
4. POTENTIALLY_RELEVANT     — anchor из potentially_relevant
5. NAVIGATION               — глобальная навигация (P-3)
6. OTHER

Смысл порядка: methodology.pdf, лежащий в меню, остаётся HIGH_VALUE и не
становится NAVIGATION из-за родительского блока. P-2/P-5 стоят выше правил
1-3 по link-taxonomy.md §5: признак чужой темы в URL надёжнее текста ссылки.
"""

import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "link_taxonomy.yaml"
RULES = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

CANDIDATE_CLASSES = {"HIGH_VALUE", "POTENTIALLY_RELEVANT"}

STOPWORDS = {"the", "and", "for", "with", "from", "rate", "hu", "mnb"}


def topic_terms(title: str) -> set[str]:
    """Термины темы страницы — пока лексически из title/h1, без LLM."""
    return {w for w in re.findall(r"[a-z]{4,}", title.lower()) if w not in STOPWORDS}


@lru_cache(maxsize=None)
def _pattern(keyword: str) -> re.Pattern:
    """Ключевое слово → regex по границам токенов.

    Разделителями считаются любые не-буквенно-цифровые символы, поэтому
    `/resolution/`, `resolution-of-the-board` и `Resolution on the CCyB rate`
    совпадают, а `mind` с `ind` — нет.
    """
    words = re.findall(r"[a-z0-9]+", keyword.lower())

    parts = [re.escape(w) for w in words]

    # ponytail: наивные множественные числа (decision(s), guideline(s),
    # methodolog(y|ies)). Стеммер — если появятся другие формы.
    last = words[-1]
    parts[-1] = (
        re.escape(last[:-1]) + "(?:y|ies)" if last.endswith("y")
        else re.escape(last) + "(?:e?s)?"
    )

    return re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(parts) + r"(?![a-z0-9])")


def matches_keyword(text: str, keyword: str) -> bool:
    return bool(_pattern(keyword).search(text.lower()))


def _first_match(keywords: list[str], text: str) -> str | None:
    return next((k for k in keywords if matches_keyword(text, k)), None)


def _extension(path: str) -> str | None:
    return next((e for e in RULES["documents"]["extensions"] if path.endswith(e)), None)


def is_ignored(url: str) -> bool:
    """P-0."""
    path = urlparse(url).path.lower()

    return any(path.endswith(e) for e in RULES["ignore_extensions"])


def classify(link: dict, topic: set[str] = frozenset()) -> dict:
    """Возвращает {"class": ..., "reason": ...}.

    reason нужен для отладки crawler'а: по нему видно, почему документ
    не был открыт или, наоборот, попал в кандидаты.
    """
    anchor = link["anchor_text"].strip().lower()
    url = link["url"].lower()
    path = urlparse(url).path
    ext = _extension(path)
    haystack = f"{path} {anchor}"
    nav = RULES["navigation"]

    # topic_match = direct: термин темы встречается в URL или в тексте ссылки
    on_topic = _first_match(sorted(topic), haystack) if topic else None

    # P-2. Чужая тема в URL/anchor побеждает anchor text
    hit = _first_match(RULES["unrelated_topic"]["patterns"], haystack)
    if hit and not on_topic:
        return {"class": "IRRELEVANT", "reason": f"matched unrelated topic: {hit}"}

    # P-5. Чужая предметная область регулятора
    hit = _first_match(RULES["foreign_domains"]["patterns"], haystack)
    if hit and not on_topic:
        return {"class": "IRRELEVANT", "reason": f"matched foreign policy domain: {hit}"}

    # 1. explicit HIGH_VALUE по тексту ссылки
    if anchor not in nav["anchors"]:
        hit = _first_match(RULES["high_value"]["anchors"], anchor)
        if hit:
            return {"class": "HIGH_VALUE", "reason": f"matched high-value anchor: {hit}"}

    # 2. explicit тип регулятивного документа в URL
    hit = _first_match(RULES["document_types"]["url_patterns"], url)
    if hit:
        # Раздел сайта в меню без темы исследования — это навигация, а не документ.
        # Файл (pdf/xlsx/docx) через это исключение не проходит: link-taxonomy.md §6.1.
        if link.get("in_nav") and not on_topic and not ext:
            return {
                "class": "NAVIGATION",
                "reason": f"site section '{hit}' inside <{link['in_nav']}> without topic match",
            }

        reason = f"matched url pattern: {hit}" + (f" + {ext.lstrip('.')}" if ext else "")
        return {"class": "HIGH_VALUE", "reason": reason}

    # 3. документ без тематического признака — кандидат, но не HIGH_VALUE
    if ext:
        return {
            "class": "POTENTIALLY_RELEVANT",
            "reason": f"document extension without topic signal: {ext.lstrip('.')}",
        }

    # 4. вероятно полезные разделы — намеренно выше NAVIGATION
    hit = _first_match(RULES["potentially_relevant"]["anchors"], anchor)
    if hit:
        return {"class": "POTENTIALLY_RELEVANT", "reason": f"matched anchor: {hit}"}

    hit = _first_match(RULES["potentially_relevant"]["section_anchors"], anchor)
    if hit:
        if link.get("in_nav") and not on_topic:
            return {
                "class": "NAVIGATION",
                "reason": f"generic section '{hit}' inside <{link['in_nav']}> without topic match",
            }

        return {"class": "POTENTIALLY_RELEVANT", "reason": f"matched anchor: {hit}"}

    # 5. глобальная навигация (P-3)
    hit = _first_match(nav["anchors"], anchor)
    if hit:
        return {
            "class": "NAVIGATION",
            "reason": f"matched global navigation anchor: {link['anchor_text'] or hit}",
        }

    hit = _first_match(nav["url_patterns"], path)
    if hit:
        return {"class": "NAVIGATION", "reason": f"matched navigation url pattern: {hit}"}

    # P-3: контейнер nav/header/footer + нет содержательных признаков.
    # Документ (pdf/xlsx/docx) сюда не доходит — он уже отработан правилом 3.
    if link.get("in_nav") and not on_topic:
        return {
            "class": "NAVIGATION",
            "reason": f"inside <{link['in_nav']}> without content signal",
        }

    return {"class": "OTHER", "reason": "no rule matched"}


def classify_all(links: list[dict], topic: set[str] = frozenset()) -> list[dict]:
    return [link | classify(link, topic) for link in links if not is_ignored(link["url"])]


def candidates(links: list[dict]) -> list[dict]:
    """P-3 filtering: остаются только исследовательские материалы."""
    return [link for link in links if link["class"] in CANDIDATE_CLASSES]
