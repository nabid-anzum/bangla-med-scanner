"""PubMed article search using the Python standard library."""

import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get_json(endpoint, params):
    parameters = dict(params)
    parameters["tool"] = "BanglaMedScanner"

    contact_email = os.environ.get(
        "BMS_NCBI_EMAIL", ""
    ).strip()

    if contact_email:
        parameters["email"] = contact_email

    url = (
        f"{API_ROOT}/{endpoint}?"
        f"{urlencode(parameters)}"
    )

    request = Request(
        url,
        headers={
            "User-Agent":
            "BanglaMedScanner/0.1 (MSc academic prototype)"
        },
    )

    with urlopen(request, timeout=12) as response:
        return json.load(response)


def search_pubmed(english_query, limit=3):
    """Search PubMed and return article metadata."""

    if (
        not isinstance(english_query, str)
        or not english_query.strip()
    ):
        raise ValueError(
            "An English-language search query is required"
        )

    limit = max(1, min(int(limit), 5))

    search_data = _get_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": english_query.strip(),
            "retmax": limit,
            "retmode": "json",
            "sort": "relevance",
        },
    )

    identifiers = search_data.get(
        "esearchresult", {}
    ).get("idlist", [])

    if not identifiers:
        return []

    summary_data = _get_json(
        "esummary.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(identifiers),
            "retmode": "json",
        },
    )

    records = summary_data.get("result", {})
    papers = []

    for pmid in identifiers:
        record = records.get(str(pmid), {})

        if not record:
            continue

        doi = next(
            (
                item.get("value", "")
                for item in record.get("articleids", [])
                if item.get("idtype") == "doi"
            ),
            "",
        )

        papers.append({
            "pmid": str(pmid),
            "title": record.get("title", ""),
            "journal": record.get(
                "fulljournalname", ""
            ),
            "date": record.get("pubdate", ""),
            "doi": doi,
            "url": (
                "https://pubmed.ncbi.nlm.nih.gov/"
                f"{pmid}/"
            ),
        })

    return papers


def main():
    if len(sys.argv) != 2:
        print(
            'Usage: python3 -m '
            'banglamedscanner.pubmed '
            '"English medical search query"'
        )
        return 2

    try:
        papers = search_pubmed(sys.argv[1])
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(
            f"PubMed request failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(
        papers,
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
