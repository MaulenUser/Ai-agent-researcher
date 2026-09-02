from bs4 import BeautifulSoup
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

# link-taxonomy.md §2.1: dom_container — имя ближайшего семантического контейнера
LANDMARKS = {"nav", "header", "footer"}

CONTAINERS = {"main", "article", "aside", "table", "li"}

SURROUNDING_TEXT_LIMIT = 300


def normalize_url(url: str) -> str:
    """Схема и хост в нижний регистр, без фрагмента, без utm-меток,
    без завершающего слэша — чтобы дедупликация не считала дублями одно и то же."""
    p = urlparse(url)

    path = p.path.rstrip("/") or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")])

    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, p.params, query, ""))


def _container(a) -> str:
    """Ближайший семантический контейнер.

    Навигационные landmark'и ищутся по всей цепочке родителей и побеждают:
    ссылка внутри <nav><ul><li> — навигация, а не список (§5 P-3).
    """
    nearest = "body"

    for parent in a.parents:
        classes = " ".join(parent.get("class", [])).lower()

        if "breadcrumb" in classes:
            return "breadcrumb"

        if parent.name in LANDMARKS or parent.get("role") == "navigation":
            return "nav" if parent.get("role") == "navigation" else parent.name

        if nearest == "body" and parent.name in CONTAINERS:
            nearest = "list" if parent.name == "li" else parent.name

    return nearest


def _context(a) -> dict:
    """Признаки F-06…F-08 (link-taxonomy.md §2.1)."""
    container = _container(a)

    # Заголовок описывает блок контента. Для ссылки в меню или подвале
    # ближайший предшествующий h1-h6 — это последний заголовок статьи,
    # к ней не относящийся: он дал бы ложный topic_match всему футеру.
    heading = a.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"]) \
        if container not in LANDMARKS | {"breadcrumb"} else None

    block = a.find_parent(["p", "li", "td", "div", "section", "article"]) or a

    return {
        "dom_container": container,
        "section_heading": heading.get_text(" ", strip=True) if heading else "",
        "surrounding_text": block.get_text(" ", strip=True)[:SURROUNDING_TEXT_LIMIT],
    }


def extract_links(html: bytes, base_url: str) -> list[dict]:
    html_text = html.decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "lxml")

    base_domain = urlparse(base_url).netloc.lower()

    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href")

        target_url = normalize_url(urljoin(base_url, href))

        parsed = urlparse(target_url)

        if parsed.scheme not in {"http", "https"}:
            continue

        anchor_text = a.get_text(" ", strip=True)

        # меню и футер повторяют одни и те же ссылки по нескольку раз
        if (target_url, anchor_text) in seen:
            continue

        seen.add((target_url, anchor_text))

        links.append({
            "url": target_url,
            "anchor_text": anchor_text,
            "same_domain": parsed.netloc == base_domain,
            "context": _context(a),
        })

    return links
