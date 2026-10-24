"""
Bibliography integrity gate.

The manuscript's references previously carried arXiv identifiers that resolved to
unrelated papers (and wrong titles/authors for others). This gate keeps every
reference in paper/PAPER_FINAL.md tied to an entry in paper/references_verified.csv
that records the title and identifier checked against the primary source.
"""

import csv
import re

MANUSCRIPT = "paper/PAPER_FINAL.md"
VERIFIED = "paper/references_verified.csv"

# Identifiers that appeared in an earlier manuscript revision and resolve to unrelated papers.
KNOWN_BAD_IDS = {"2601.07506", "2408.12885", "2410.15079"}


def _load_verified():
    with open(VERIFIED, newline="") as f:
        return list(csv.DictReader(f))


def _references_section():
    text = open(MANUSCRIPT).read()
    assert "## References" in text, "Manuscript has no References section"
    return text.split("## References", 1)[1]


def test_no_known_bad_arxiv_ids():
    text = open(MANUSCRIPT).read()
    for bad in KNOWN_BAD_IDS:
        assert bad not in text, f"Manuscript still cites mismatched arXiv id {bad}"


def test_every_arxiv_id_in_references_is_verified():
    refs = _references_section()
    ids_in_manuscript = set(re.findall(r"arXiv:(\d{4}\.\d{4,5})", refs))
    assert ids_in_manuscript, "No arXiv identifiers found in References"
    verified = {r["arxiv_id"]: r for r in _load_verified() if r["arxiv_id"]}
    missing = ids_in_manuscript - set(verified)
    assert not missing, f"arXiv ids cited but not in references_verified.csv: {sorted(missing)}"
    for i in ids_in_manuscript:
        assert verified[i]["status"] == "VERIFIED_PRIMARY", f"{i} is not VERIFIED_PRIMARY"


def test_reference_titles_match_verified_titles():
    """Each verified paper's title must appear verbatim in the manuscript References."""
    refs = _references_section()
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    refs_n = norm(refs)
    for row in _load_verified():
        if row["status"] == "VERIFIED_PRIMARY":
            assert norm(row["title"]) in refs_n, f"Title mismatch or missing in References: {row['title']}"


def test_verified_references_are_cited_in_body():
    """Every verified paper should actually be cited somewhere in the body."""
    text = open(MANUSCRIPT).read()
    body = text.split("## References", 1)[0]
    markers = {
        "alzahrani2024": "Alzahrani", "barazandeh2026": "Barazandeh", "casola2025": "Casola",
        "holzer2025": "Holzer", "jeong2026": "Jeong", "kim2026": "Kim", "koussios2026": "Koussios",
        "li2026falsification": "Li & Hai", "li2025ilr": "Li et al. (2025)", "liu2026ces": "Liu et al.",
        "wataoka2024": "Wataoka", "wu2026": "Wu et al.", "yang2026": "Yang et al.", "zheng2023": "Zheng",
    }
    for key, marker in markers.items():
        assert marker in body, f"Reference {key} ('{marker}') is not cited in the manuscript body"
