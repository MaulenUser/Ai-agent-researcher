"""Пакетная классификация ссылок со всех seed URL -> Excel-совместимый CSV.

Обход в глубину не выполняется (T-010): классифицируются только ссылки,
непосредственно найденные на seed-страницах, найденные URL не загружаются.

    py -3.10 -m app.export_link_classification \
        --question "What is the current CCyB rate and how is it set?" \
        --seeds ../source/links.md \
        --output data/results/link_classification.csv
"""

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path

from app.fetcher import fetch_url
from app.html_parser import parse_html
from app.link_extractor import extract_links, normalize_url
from app.taxonomy import classify, is_ignored

COLUMNS = [
    "research_question", "seed_url", "final_seed_url", "seed_http_status",
    "seed_content_type", "source_page_title", "target_url", "anchor_text",
    "same_domain", "dom_container", "section_heading", "surrounding_text",
    "status", "class", "rule", "reason", "error",
]

# URL в Markdown идут голым текстом, иногда с комментарием следом:
# `...measures.pdf -стр 7`, `...anticiclico/ (Banco de España)`.
URL_RE = re.compile(r"https?://[^\s<>\"'\]\)]+")


def read_seeds(path: Path) -> list[str]:
    """URL из Markdown, нормализованные, без точных дублей, в порядке появления."""
    seen = {}

    for raw in URL_RE.findall(path.read_text(encoding="utf-8")):
        seen.setdefault(normalize_url(raw.rstrip(".,;:")), None)

    return list(seen)


def _source_page_topic(parsed: dict) -> str:
    h1 = next((h["text"] for h in parsed["headings"] if h["level"] == "h1"), "")

    return f"{parsed['title'] or ''} {h1}".strip()


async def process_seed(seed_url: str, question: str) -> list[dict]:
    base = {"research_question": question, "seed_url": seed_url}

    try:
        result = await fetch_url(seed_url)
    except Exception as exc:
        return [base | {"status": "FETCH_ERROR",
                        "error": f"{type(exc).__name__}: {exc}"}]

    base |= {
        "final_seed_url": result["final_url"],
        "seed_http_status": result["status_code"],
        "seed_content_type": result["content_type"] or "",
    }

    # httpx на 4xx/5xx не бросает, а тело ошибки — HTML без ссылок:
    # без этой проверки seed молча исчез бы из выгрузки (dnb.nl отдаёт 403).
    if result["status_code"] >= 400:
        return [base | {"status": "FETCH_ERROR",
                        "error": f"HTTP {result['status_code']}"}]

    if "text/html" not in (result["content_type"] or ""):
        return [base | {"status": "UNSUPPORTED_SEED_CONTENT_TYPE"}]

    parsed = parse_html(result["content"], result["final_url"])
    base["source_page_title"] = parsed["title"] or ""
    topic = _source_page_topic(parsed)

    rows = []

    for link in extract_links(result["content"], result["final_url"]):
        row = base | {
            "target_url": link["url"],
            "anchor_text": link["anchor_text"],
            "same_domain": link["same_domain"],
            **link["context"],
        }

        if is_ignored(link["url"]):
            rows.append(row | {"status": "IGNORED", "class": "", "rule": "P-0",
                               "reason": "filtered by P-0: non-content asset"})
            continue

        rows.append(row | {"status": "CLASSIFIED"} | classify(link, question, topic))

    return rows


async def main(argv=None) -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True,
                        help="research question: класс ссылки зависит от него")
    parser.add_argument("--seeds", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    seeds = read_seeds(args.seeds)
    print(f"seeds after dedup: {len(seeds)}")

    rows = []

    # Последовательно: параллельная загрузка создаёт лишнюю нагрузку на сайты
    # регуляторов, а объём seed-списка того не требует.
    for i, seed in enumerate(seeds, 1):
        seed_rows = await process_seed(seed, args.question)
        rows += seed_rows
        status = seed_rows[0]["status"] if seed_rows else "NO_LINKS"
        print(f"[{i}/{len(seeds)}] {status:32} {len(seed_rows):4} rows  {seed}")

    write_csv(rows, args.output)

    print(f"\n{len(rows)} rows -> {args.output}")

    for field in ("status", "class"):
        print(f"\nby {field}:")
        counts = {}
        for row in rows:
            counts[row.get(field) or "-"] = counts.get(row.get(field) or "-", 0) + 1
        for key, count in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {key}: {count}")


def write_csv(rows: list[dict], output: Path) -> None:
    """utf-8-sig + `;`: Excel иначе не распознаёт кодировку и колонки."""
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows({c: row.get(c, "") for c in COLUMNS} for row in rows)


if __name__ == "__main__":
    asyncio.run(main())
