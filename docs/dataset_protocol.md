# BanglaMedScanner Pilot Corpus Collection Protocol

The 100-paper pilot corpus is collected automatically from PubMed via NCBI ESearch and EFetch.
Five clinical topics each contribute 20 English-language papers: type 2 diabetes,
hypertension, asthma, depression, and COPD. Search filters require an abstract,
human studies, publication since January 1, 2021, and an RCT, meta-analysis,
or systematic-review publication type. Results are relevance-ranked, deduplicated,
and frozen by PMID at collection time; the manifest records exact queries and time.

Local `data/corpus.sqlite3` stores abstracts for indexing and experimental use.
`datasets/pmids.csv` and `datasets/collection_manifest.json` contain only
identifiers and collection metadata, not abstract text, and can be published.

Per topic, 16 records are assigned to development and four to evaluation candidates
using a deterministic PMID hash. These are **not gold-standard annotations**.
Independent evidence-label verification is required before precision, recall,
extraction accuracy, or factual-consistency claims can be made. Automated
collection does not imply systematic-review coverage or clinical validity.

PubMed abstracts may be copyrighted. Do not redistribute the local database
or display full abstracts in a public application without checking rights.
The project is for research assistance, not medical advice.

