import asyncio
import csv

from app import export_link_classification as ex

QUESTION = "What is the current CCyB rate and how is it set?"

MARKDOWN = """# Ссылки

  https://www.mnb.hu/en/page/ (комментарий)
  https://www.mnb.hu/en/page
  https://www.cnb.cz/en/report.pdf -стр 7
"""

HTML = b"""<html><head><title>Countercyclical capital buffer</title></head><body>
<main>
  <h1>Countercyclical capital buffer</h1>
  <p><a href="/en/ccyb-methodology-q42024-en.pdf">CCyB methodology</a></p>
  <p><a href="/en/logo.png">logo</a></p>
</main></body></html>"""


def test_read_seeds_dedups(tmp_path):
    md = tmp_path / "links.md"
    md.write_text(MARKDOWN, encoding="utf-8")

    # `page/` и `page` — один URL после normalize_url; хвост `-стр 7` не попадает в URL
    assert ex.read_seeds(md) == [
        "https://www.mnb.hu/en/page",
        "https://www.cnb.cz/en/report.pdf",
    ]


def test_rows_and_csv_roundtrip(tmp_path, monkeypatch):
    async def fake_fetch(url):
        return {"requested_url": url, "final_url": "https://www.mnb.hu/en/ccyb",
                "status_code": 200, "content_type": "text/html; charset=utf-8",
                "content": HTML}

    monkeypatch.setattr(ex, "fetch_url", fake_fetch)

    rows = asyncio.run(ex.process_seed("https://www.mnb.hu/en/ccyb", QUESTION))

    by_url = {row["target_url"]: row for row in rows}

    methodology = by_url["https://www.mnb.hu/en/ccyb-methodology-q42024-en.pdf"]
    assert methodology["status"] == "CLASSIFIED"
    assert methodology["class"] == "HIGH_VALUE"
    assert methodology["source_page_title"] == "Countercyclical capital buffer"

    image = by_url["https://www.mnb.hu/en/logo.png"]
    assert (image["status"], image["class"], image["rule"]) == ("IGNORED", "", "P-0")

    out = tmp_path / "results" / "link_classification.csv"
    ex.write_csv(rows, out)

    with out.open(encoding="utf-8-sig", newline="") as f:
        read_back = list(csv.DictReader(f, delimiter=";"))

    assert list(read_back[0]) == ex.COLUMNS
    assert {r["target_url"] for r in read_back} == set(by_url)
