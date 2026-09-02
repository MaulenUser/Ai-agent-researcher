from bs4 import BeautifulSoup
import trafilatura


def parse_html(html: bytes, url: str) -> dict:
    html_text = html.decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "lxml")

    title = soup.title.get_text(strip=True) if soup.title else None

    main_text = trafilatura.extract(
        html_text,
        url=url,
        include_links=False,
        include_tables=True,
    )

    headings = []

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(" ", strip=True)

        if text:
            headings.append({
                "level": tag.name,
                "text": text,
            })

    return {
        "title": title,
        "headings": headings,
        "text": main_text or "",
    }