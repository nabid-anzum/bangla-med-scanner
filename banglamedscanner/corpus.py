"""Reproducible PubMed abstract corpus for research; no external Python packages."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "corpus.sqlite3"
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOPICS = [
    ("diabetes", '"Diabetes Mellitus, Type 2"[MeSH Terms] OR "type 2 diabetes"[Title/Abstract]'),
    ("hypertension", '"Hypertension"[MeSH Terms] OR hypertension[Title/Abstract]'),
    ("asthma", '"Asthma"[MeSH Terms] OR asthma[Title/Abstract]'),
    ("depression", '"Depressive Disorder"[MeSH Terms] OR depression[Title/Abstract]'),
    ("copd", '"Pulmonary Disease, Chronic Obstructive"[MeSH Terms] OR COPD[Title/Abstract]'),
]


def _request(endpoint, params):
    p = dict(params)
    p["tool"] = "BanglaMedScanner"
    if os.environ.get("BMS_NCBI_EMAIL", "").strip():
        p["email"] = os.environ["BMS_NCBI_EMAIL"].strip()
    url = f"{NCBI}/{endpoint}?{urlencode(p)}"
    for attempt in range(4):
        time.sleep(0.8)  # below NCBI's three-request/second unauthenticated limit
        try:
            with urlopen(Request(url, headers={"User-Agent": "BanglaMedScanner/0.2 (MSc research)"}), timeout=25) as resp:
                return resp.read()
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except (TimeoutError, URLError):
            if attempt == 3:
                raise
        time.sleep(2 ** attempt * 2)
    raise RuntimeError("NCBI request failed")


def _text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def parse_articles(xml_bytes):
    root = ET.fromstring(xml_bytes)
    records = []
    for item in root.findall("./PubmedArticle"):
        citation = item.find("MedlineCitation")
        if citation is None:
            continue
        article = citation.find("Article")
        if article is None:
            continue
        pmid = _text(citation.find("PMID"))
        title = _text(article.find("ArticleTitle"))
        blocks = []
        for a in article.findall("./Abstract/AbstractText"):
            label = a.get("Label") or a.get("NlmCategory") or ""
            chunk = _text(a)
            if chunk:
                blocks.append(f"{label}: {chunk}" if label else chunk)
        abstract = "\n".join(blocks)
        lang = [_text(e).lower() for e in article.findall("./Language")]
        pub_date = article.find("./Journal/JournalIssue/PubDate")
        year_text = _text(pub_date.find("Year")) if pub_date is not None else ""
        if not year_text and pub_date is not None:
            match = re.search(r"\b(?:19|20)\d{2}\b", _text(pub_date.find("MedlineDate")))
            year_text = match.group() if match else ""
        if not year_text:
            year_text = _text(article.find("./ArticleDate/Year"))
        types = [_text(e) for e in article.findall("./PublicationTypeList/PublicationType")]
        if not (pmid.isdigit() and title and len(abstract) >= 120 and year_text.isdigit()):
            continue
        if lang and "eng" not in lang:
            continue
        if any("retract" in p.lower() for p in types):
            continue
        doi, pmcid = "", ""
        for e in item.findall("./PubmedData/ArticleIdList/ArticleId"):
            if e.get("IdType") == "doi":
                doi = _text(e)
            elif e.get("IdType") == "pmc":
                pmcid = _text(e)
        if not doi:
            for e in article.findall("./ELocationID"):
                if e.get("EIdType") == "doi":
                    doi = _text(e)
                    break
        records.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "journal": _text(article.find("./Journal/Title")),
            "year": int(year_text),
            "doi": doi,
            "pmcid": pmcid,
            "study_type": "; ".join(types),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return records


def collect(out_db, out_csv, out_manifest):
    for path in (out_db, out_csv, out_manifest):
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"Refusing to overwrite: {path}")
    today = datetime.now(timezone.utc).date().isoformat()
    collected = datetime.now(timezone.utc).isoformat()
    seen = set()
    records = []
    queries = {}
    for topic, keywords in TOPICS:
        query = (
            f"({keywords}) AND english[Language] AND hasabstract "
            'AND "Humans"[MeSH Terms] AND '
            '("Randomized Controlled Trial"[Publication Type] OR '
            '"Meta-Analysis"[Publication Type] OR '
            '"Systematic Review"[Publication Type]) '
            f'AND ("2021/01/01"[Date - Publication] : "{today}"[Date - Publication]) '
        )
        queries[topic] = query
        search = json.loads(_request("esearch.fcgi", {
            "db": "pubmed", "term": query, "retmax": 100,
            "retmode": "json", "sort": "relevance",
        }))
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            raise RuntimeError(f"PubMed returned no IDs for {topic}")
        xml = _request("efetch.fcgi", {
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
        })
        accepted = 0
        for paper in parse_articles(xml):
            if paper["pmid"] in seen or not 2021 <= paper["year"] <= int(today[:4]):
                continue
            paper["topic"] = topic
            seen.add(paper["pmid"])
            records.append(paper)
            accepted += 1
            if accepted == 20:
                break
        print(f"{topic}: {accepted}/20 papers collected", flush=True)
        if accepted < 20:
            raise RuntimeError(f"Insufficient qualifying articles for {topic}: {accepted}")
    assert len(records) == 100
    # Stable split per topic: 16 development, 4 held-out review candidates.
    for topic, _ in TOPICS:
        subset = sorted((p for p in records if p["topic"] == topic),
                        key=lambda p: hashlib.sha256(p["pmid"].encode()).hexdigest())
        for i, paper in enumerate(subset):
            paper["split"] = "evaluation_candidate" if i < 4 else "development"
    with sqlite3.connect(out_db) as db:
        db.execute("""CREATE TABLE papers (
            pmid TEXT PRIMARY KEY, topic TEXT NOT NULL, title TEXT NOT NULL,
            abstract TEXT NOT NULL, journal TEXT, year INTEGER,
            doi TEXT, pmcid TEXT, study_type TEXT, url TEXT,
            split TEXT, retrieved_at_utc TEXT)""")
        db.execute("CREATE VIRTUAL TABLE papers_fts USING fts5(title, abstract)")
        for p in records:
            cur = db.execute("""INSERT INTO papers
                (pmid, topic, title, abstract, journal, year, doi, pmcid,
                 study_type, url, split, retrieved_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                p["pmid"], p["topic"], p["title"], p["abstract"],
                p["journal"], p["year"], p["doi"], p["pmcid"],
                p["study_type"], p["url"], p["split"], collected,
            ))
            db.execute("INSERT INTO papers_fts(rowid, title, abstract) VALUES (?, ?, ?)",
                       (cur.lastrowid, p["title"], p["abstract"]))
        assert db.execute("SELECT count(*) FROM papers").fetchone()[0] == 100
        assert db.execute("SELECT count(*) FROM papers_fts").fetchone()[0] == 100
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pmid", "topic", "split", "year", "url"])
        for paper in records:
            writer.writerow([paper[k] for k in ("pmid", "topic", "split", "year", "url")])
    ids_sha = hashlib.sha256("\n".join(p["pmid"] for p in records).encode()).hexdigest()
    manifest = {
        "title": "BanglaMedScanner pilot corpus", "retrieved_at_utc": collected,
        "source": "NCBI PubMed E-utilities ESearch and EFetch",
        "date_range": ["2021-01-01", today], "total_papers": 100,
        "selection": "20 English-language abstracts per clinical topic; relevance-ranked search",
        "topics": {name: 20 for name, _ in TOPICS},
        "splits": {"development": 80, "evaluation_candidate": 20},
        "pmid_list_sha256": ids_sha, "queries": queries,
        "warning": "Evaluation candidates are NOT manually verified gold labels. Abstracts are not redistributed in this manifest.",
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def stats(db_path=DEFAULT_DB):
    with sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True) as db:
        return {
            "total": db.execute("SELECT count(*) FROM papers").fetchone()[0],
            "by_topic": dict(db.execute("SELECT topic, count(*) FROM papers GROUP BY topic")),
            "by_split": dict(db.execute("SELECT split, count(*) FROM papers GROUP BY split")),
        }


def local_search(query, limit=5, db_path=DEFAULT_DB):
    terms = re.findall(r"[A-Za-z][A-Za-z0-9]{1,}", query)[:12]
    if not terms:
        return []
    match = " OR ".join('"' + x + '"' for x in terms)
    with sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""SELECT p.pmid, p.title, p.journal, p.year,
            p.doi, p.pmcid, p.url, p.topic, p.split
            FROM papers_fts JOIN papers p ON p.rowid = papers_fts.rowid
            WHERE papers_fts MATCH ? ORDER BY bm25(papers_fts) LIMIT ?""",
            (match, min(max(1, int(limit)), 20)),
        ).fetchall()
        return [dict(r) for r in rows]


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--db", type=Path, required=True)
    build.add_argument("--index", type=Path, required=True)
    build.add_argument("--manifest", type=Path, required=True)
    sub.add_parser("stats")
    search = sub.add_parser("search")
    search.add_argument("query")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(collect(args.db, args.index, args.manifest), indent=2))
    elif args.cmd == "stats":
        print(json.dumps(stats(), indent=2))
    else:
        print(json.dumps(local_search(args.query), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

