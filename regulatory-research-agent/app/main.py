import asyncio
import sys

from app.fetcher import fetch_url
from app.html_parser import parse_html
from app.link_extractor import extract_links
from app.taxonomy import candidates, classify_all, topic_terms


URL = (
    "https://www.mnb.hu/en/financial-stability/"
    "macroprudential-policy/the-macroprudential-toolkit/"
    "countercyclical-capital-buffer-ccyb"
)


async def main():
    # консоль Windows по умолчанию cp1251 и падает на венгерских буквах
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    result = await fetch_url(URL)

    print("HTTP:", result["status_code"])
    print("Content-Type:", result["content_type"])
    print("Final URL:", result["final_url"])

    if "text/html" not in (result["content_type"] or ""):
        return

    parsed = parse_html(
        result["content"],
        result["final_url"],
    )

    topic = topic_terms(parsed["title"] or "")

    links = classify_all(
        extract_links(result["content"], result["final_url"]),
        topic,
    )

    print("\nTITLE:")
    print(parsed["title"])

    print("\nHEADINGS:")
    for heading in parsed["headings"]:
        print(heading)

    print("\nTEXT:")
    print(parsed["text"][:3000])

    print("\nTOPIC TERMS:", ", ".join(sorted(topic)))

    print("\nLINKS:", len(links))

    for name in ("HIGH_VALUE", "POTENTIALLY_RELEVANT", "NAVIGATION", "IRRELEVANT", "OTHER"):
        print(f"  {name}: {sum(1 for l in links if l['class'] == name)}")

    keep = candidates(links)

    print("\nCANDIDATE LINKS:", len(keep))

    for link in keep:
        print(f"[{link['class']}] {link['anchor_text'][:60]!r} -> {link['url']}")
        print(f"    reason: {link['reason']}")

    print("\nFILTERED OUT:")

    for link in links:
        if link not in keep:
            print(f"[{link['class']}] {link['anchor_text'][:60]!r} -> {link['url']}")
            print(f"    reason: {link['reason']}")


if __name__ == "__main__":
    asyncio.run(main())