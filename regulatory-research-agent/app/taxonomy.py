"""Классификация ссылок по спецификации docs2/01_PRODUCT/link-taxonomy.md v1.0.0.

Схема §0: признаки -> семантическая группа (§4) -> класс (матрица §6).
Класс — функция группы и тематического совпадения с research_question, а не
свойство строки anchor text.

Порядок правил §5: P-0, P-1, P-2, P-4, P-3, P-5, P-6.

Единственное отклонение от нумерации §5 — P-4 (разрешение обобщённого anchor
по контексту) выполняется до P-3. Иначе LC-17 недостижим: P-3 сработал бы на
`More information` в подвале и вернул NAVIGATION, тогда как §12 ожидает
UNKNOWN. P-4 не назначает класс, он вычисляет признаки, от которых зависит
предусловие P-3 («группа»), поэтому обязан идти раньше. Зафиксировать как
уточнение §5 при следующем возврате к БА.
"""

import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "link_taxonomy.yaml"
RULES = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

GROUPS = RULES["groups"]
EXTENSIONS = RULES["extensions"]
AUTHORITY = RULES["domain_authority"]

CANDIDATE_CLASSES = {"HIGH_VALUE", "POTENTIALLY_RELEVANT"}

# §6. Матрица «ранг группы x тематическое совпадение». Структура таксономии,
# а не справочник: её изменение — возврат к БА (§8), поэтому она в коде.
MATRIX = {
    "primary":    {"direct": "HIGH_VALUE", "partial": "HIGH_VALUE", "none": "POTENTIALLY_RELEVANT"},
    "secondary":  {"direct": "HIGH_VALUE", "partial": "POTENTIALLY_RELEVANT", "none": "POTENTIALLY_RELEVANT"},
    "navigation": {"direct": "POTENTIALLY_RELEVANT", "partial": "NAVIGATION", "none": "NAVIGATION"},
    "unrelated":  {"direct": "UNKNOWN", "partial": "IRRELEVANT", "none": "IRRELEVANT"},
    None:         {"direct": "POTENTIALLY_RELEVANT", "partial": "POTENTIALLY_RELEVANT", "none": "UNKNOWN"},
}


# --- сопоставление строк (§11: подстрока и шаблон, а не точное равенство) ---

@lru_cache(maxsize=None)
def _anchor_re(keyword: str) -> re.Pattern:
    """Ключевое слово -> regex по границам токенов с наивным мн. числом.

    `/resolution/`, `resolution-of-the-board` и `Resolution on the rate`
    совпадают, `mind` с `ind` — нет, `decision` с `decisions` — да.
    """
    words = re.findall(r"[a-z0-9]+", keyword.lower())
    parts = [re.escape(w) for w in words]

    last = words[-1]
    parts[-1] = (
        re.escape(last[:-1]) + "(?:y|ies)" if last.endswith("y")
        else re.escape(last) + "(?:e?s)?"
    )

    return re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(parts) + r"(?![a-z0-9])")


@lru_cache(maxsize=None)
def _url_re(pattern: str) -> re.Pattern:
    """Шаблон URL — от границы токена, но без правой границы:
    `methodolog` обязан совпасть с `/letoltes/ccyb-methodology-q42024-en.pdf`."""
    words = re.findall(r"[a-z0-9]+", pattern.lower())

    return re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(re.escape(w) for w in words))


def matches_keyword(text: str, keyword: str) -> bool:
    return bool(_anchor_re(keyword).search(text.lower()))


def _first(keywords, text: str, matcher=matches_keyword) -> str | None:
    return next((k for k in keywords if matcher(text, k)), None)


def _url_hit(path: str, patterns) -> str | None:
    return next((p for p in patterns if _url_re(p).search(path.lower())), None)


# --- §3. research_question -> Q (термины вопроса) и V (предметная лексика) ---

@lru_cache(maxsize=None)
def normalize_question(question: str) -> frozenset[str]:
    tokens = [t for t in re.findall(r"[a-z0-9-]+", question.lower())
              if t not in RULES["stopwords"]]

    terms = set(tokens)
    ngrams = set(tokens) | {" ".join(p) for p in zip(tokens, tokens[1:])}

    for key, synonyms in RULES["synonyms"].items():
        family = {key.lower()} | {s.lower() for s in synonyms}

        if ngrams & family:
            terms |= family

    return frozenset(terms)


VOCABULARY = frozenset(RULES["domain_vocabulary"])


def _topic_match(direct_text: str, weak_text: str, q: frozenset[str]) -> str:
    """§3 + §6.2: заголовок и URL дают direct, окружение и тема страницы — только partial."""
    if _first(q, direct_text):
        return "direct"

    if _first(VOCABULARY, direct_text) or _first(q | VOCABULARY, weak_text):
        return "partial"

    return "none"


# --- §4. Группа ---

def _extension(path: str) -> str | None:
    return path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else None


def _match_group(anchor: str, path: str, ext: str | None) -> tuple[str, int] | None:
    """Возвращает (имя группы, сила признака: 2 сильный / 1 слабый).

    Tie-break §4: сильный побеждает слабый, при равной силе — порядок групп.
    """
    best = None

    for name, group in GROUPS.items():
        if _first(group["anchor_strong"], anchor) or _url_hit(path, group["url_patterns"]):
            strength = 2
        elif _first(group["anchor_weak"], anchor):
            strength = 1
        else:
            continue

        # §6.1: pdf повышает слабый признак документа до сильного
        if strength == 1 and ext in EXTENSIONS["document"]:
            strength = 2

        if best is None or strength > best[1]:
            best = (name, strength)

    # §6.1: xlsx/csv/zip принудительно назначают группу data, если сильнее не нашлось
    if best is None and ext in EXTENSIONS["data"]:
        return ("data", 1)

    return best


# --- P-0 ---

def is_ignored(url: str) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return True

    return _extension(parsed.path.lower()) in EXTENSIONS["ignore"]


def _bucket(host: str, bucket: str) -> str | None:
    return next((d for d in AUTHORITY[bucket] if host == d or host.endswith("." + d)), None)


def classify(link: dict, research_question: str = "", source_page_topic: str = "") -> dict:
    """Возвращает {"class", "rule", "reason"}.

    rule — идентификатор сработавшего правила §5/§6, без него неисполним
    процесс обновления справочника §10 и не проверяется критерий §12.3
    («ни один IRRELEVANT не выдан по остаточному принципу»).
    """
    context = link.get("context") or {}
    anchor = link["anchor_text"]
    url = link["url"]
    parsed = urlparse(url)
    path = parsed.path.lower()
    ext = _extension(path)
    heading = context.get("section_heading", "")
    surrounding = context.get("surrounding_text", "")
    container = (context.get("dom_container") or "").lower()

    q = normalize_question(research_question)

    # Тема страницы-источника (F-09) поднимает topic_match только для ссылок
    # в контенте: меню и подвал повторяются на всех страницах сайта и темы
    # конкретной страницы не наследуют.
    inherited = "" if container in RULES["navigation_containers"] else source_page_topic

    topic = _topic_match(f"{anchor} {path} {heading}", f"{surrounding} {inherited}", q)

    # P-1. Исключённый внешний домен
    hit = _bucket(parsed.netloc.lower(), "excluded")
    if hit:
        return {"class": "IRRELEVANT", "rule": "P-1", "reason": f"excluded domain: {hit}"}

    # P-2. Признак чужой темы в URL path побеждает anchor text
    hit = _url_hit(path, GROUPS["unrelated_topic"]["url_patterns"])
    if hit:
        if _first(q, path):
            return {"class": "UNKNOWN", "rule": "P-2 exception",
                    "reason": f"unrelated topic '{hit}' and question term both in url path"}

        return {"class": "IRRELEVANT", "rule": "P-2",
                "reason": f"unrelated topic in url path: {hit}"}

    # P-4. Обобщённый или пустой anchor разрешается по контексту
    generic = not anchor.strip() or _first(RULES["generic_anchors"], anchor)
    if generic:
        group = (_match_group(heading, "", ext)
                 or _match_group(surrounding, "", ext)
                 or _match_group("", path, ext))

        if group is None:
            return {"class": "UNKNOWN", "rule": "P-4",
                    "reason": f"generic anchor '{anchor or ''}' and no group in heading, "
                              "surrounding text or url"}
    else:
        group = _match_group(anchor, path, ext)

    name, _ = group if group else (None, 0)
    rank = GROUPS[name]["rank"] if name else None

    # P-3. Служебная навигация
    if (container in RULES["navigation_containers"]
            and name in {None, "navigation", "related_material"}
            and topic != "direct"
            and ext not in EXTENSIONS["document"]):
        return {"class": "NAVIGATION", "rule": "P-3",
                "reason": f"group '{name}' inside <{container}> without direct topic match"}

    # P-5. Чужая предметная область
    hit = _first(RULES["foreign_domains"], f"{anchor} {path}")
    if hit and topic != "direct":
        return {"class": "IRRELEVANT", "rule": "P-5",
                "reason": f"foreign policy domain '{hit}' with topic_match = {topic}"}

    # P-6. Матрица §6
    cls = MATRIX[rank][topic]
    reason = f"group {name or 'undefined'} ({rank or 'undefined'}) x topic_match {topic}"

    # §6.3. Авторитетность внешнего источника
    if (cls == "HIGH_VALUE" and not link.get("same_domain", True)
            and not _bucket(parsed.netloc.lower(), "authoritative")):
        return {"class": "POTENTIALLY_RELEVANT", "rule": "P-6 + 6.3",
                "reason": f"{reason}; downgraded: neutral external domain"}

    return {"class": cls, "rule": "P-6", "reason": reason}


def classify_all(links: list[dict], research_question: str = "",
                 source_page_topic: str = "") -> list[dict]:
    return [link | classify(link, research_question, source_page_topic)
            for link in links if not is_ignored(link["url"])]


def candidates(links: list[dict]) -> list[dict]:
    """Материалы для обхода. Политика обхода UNKNOWN — за БА (OQ-029)."""
    return [link for link in links if link["class"] in CANDIDATE_CLASSES]
