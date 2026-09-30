# Corpus Versions

Two corpora exist. Results measured on one are **not comparable** with the other.

## v1: July 2026 corpus (all results in FINDINGS.md, `eval/*.xlsx`, `eval/*_results.md`)
- **Files (10 ingestible + 1 skipped):**
  - Introduction to OS.pptx
  - Process abstractions.pptx
  - Process API.pptx
  - Process execution mechanism.pptx
  - Shell programming.pptx
  - process abstraction.pdf
  - process API.pdf
  - process execution mechanism.pdf
  - Linux commands (1).pdf
  - Shell programming - sample excersice.docx (converted from the `.doc` during F11)
  - The legacy `.doc` itself is not ingestible.
- **Coverage:** processes and shell only.
- **"22 documents" reconciled:** FINDINGS F11 states "corpus 9 → 22 **Documents**". The unit is extracted `Document` objects, not files. There were 9 files, plus the converted `.docx`, which the extractor splits into 13 section Documents: 9 + 13 = 22. So "22-document corpus" (lines 276, 609, 950 of FINDINGS.md) means 22 Document objects from 10 files. It is not a count of 22 separate source documents.
- **Index snapshot:** `data/_backup_20260930/index/` (dated 2026-07-24) holds the pre-F11 index: 9 doc_ids and 1,110 chunks, under an older chunking configuration. The July evaluation runs after F11 must therefore have used indexes rebuilt at run time, and those indexes were not preserved. The exact chunk sets used in the July runs cannot be reconstructed from the files on disk.
- **Question set:** `eval/eval_set.json`, 26 hand-authored questions, each tied to v1 slide IDs.

## v2: 2026-09-30 corpus (current `data/raw`, `data/index`)
- **Source:** the user's `Theory.zip` ("complete OS data"), merged additively with v1. Details are in `docs/SOURCE_OF_TRUTH_INVENTORY.md` §8.
- **Files:** 37 in `data/raw`; 36 indexed (the legacy `.doc` is skipped; its `.docx` twin is indexed).
- **Coverage:** processes, memory (segmentation, paging, advanced page tables, demand paging, virtual memory, allocation algorithms), concurrency (threads, locks, condition variables, semaphores, concurrency bugs, deadlock, dining philosophers, reader-writer, IPC) and shell.
- **Index:** 3,646 chunks. Dense, FAISS and BM25 have identical chunk ids (verified 2026-09-30). Chunking signature `0d3703d0bd29c1dd`; embedding model `BAAI/bge-large-en-v1.5`.
- **Known duplicates / versions:**
  - `Introduction to OS.pptx` (10 slides) vs `1. Introduction to OS.pptx` (20 slides)
  - `paging (1).pptx` vs `15. Paging.pptx`
  - PDF+PPTX pairs for the three process lectures
  - `Reader writer problem` and `dining philospher` each exist as both `.pdf` and `.docx`
  - Deduplicate, or control for these, before running any retrieval experiment.
- **Question set:** none yet. The v1 set covers only processes and shell and cites v1 slide IDs, some of which have now been re-chunked.

## Rule
Do not report v1 numbers as properties of the current system. Any claim carried over from FINDINGS.md must be re-measured on v2 with a new, independently reviewed question set.
