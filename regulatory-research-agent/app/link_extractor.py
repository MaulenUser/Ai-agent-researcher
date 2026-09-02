from bs4 import BeautifulSoup
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

LANDMARKS = {"nav", "footer", "header"}


def normalize_url(url: str) -> str:
    """Схема и хост в нижний регистр, без фрагмента, без utm-меток,
    без завершающего слэша — чтобы дедупликация не считала дублями одно и то же."""
    p = urlparse(url)

    path = p.path.rstrip("/") or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")])

    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, p.params, query, ""))


def _context(a) -> tuple[str | None, str]:
    """Родительский контекст ссылки: landmark-блок и ближайший заголовок выше."""
    landmark = next((p.name for p in a.parents if p.name in LANDMARKS), None)

    heading = a.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])

    return landmark, heading.get_text(" ", strip=True) if heading else ""


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

        landmark, heading = _context(a)

        links.append({
            "url": target_url,
            "anchor_text": anchor_text,
            "same_domain": parsed.netloc == base_domain,
            "in_nav": landmark,
            "context": heading,
        })

    return links
