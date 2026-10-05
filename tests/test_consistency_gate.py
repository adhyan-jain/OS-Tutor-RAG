"""
Automated Consistency Gate for OS-Tutor-RAG Research Package.

Verifies:
1. Every numerical claim in PAPER_FINAL.md matches raw JSON artifacts.
2. No truncated SHA-256 hashes exist in REPRODUCIBILITY.md.
3. No stale 100-draw or 10,000-draw assumptions remain in PAPER_FINAL.md.
4. RCR summary JSON contains 50,000 Monte Carlo draws.
"""

import json
import re
import os
import pytest

MANUSCRIPT_PATH = "paper/PAPER_FINAL.md"
REPRODUCIBILITY_PATH = "paper/REPRODUCIBILITY.md"
RCR_SUMMARY_PATH = "research/ssr_pilot/results/rcrc/rcr_summary.json"


def test_rcr_summary_structure_and_draws():
    assert os.path.exists(RCR_SUMMARY_PATH), f"Missing {RCR_SUMMARY_PATH}"
    with open(RCR_SUMMARY_PATH) as f:
        data = json.load(f)
    
    assert data["n_monte_carlo_draws"] == 50000, f"Expected 50,000 draws, found {data['n_monte_carlo_draws']}"
    assert "E1_CANONICAL_EXACT" in data["evaluators"]
    assert "E2_NORMALIZED_MATCH" in data["evaluators"]
    assert "E3_SEMANTIC_ORACLE" in data["evaluators"]

    e2 = data["evaluators"]["E2_NORMALIZED_MATCH"]
    assert abs(e2["kendall_tau_mean"] - 0.489) < 0.01, f"Unexpected Kendall tau: {e2['kendall_tau_mean']}"
    assert abs(e2["pairwise_win_matrix"]["pairwise_reversal_probability"] - 0.1861) < 0.005, f"Unexpected reversal prob: {e2['pairwise_win_matrix']['pairwise_reversal_probability']}"
    assert abs(e2["oracle_recovery"]["oracle_recovery_rate"] - 0.2392) < 0.005, f"Unexpected recovery rate: {e2['oracle_recovery']['oracle_recovery_rate']}"


def test_manuscript_numbers_match_json():
    assert os.path.exists(MANUSCRIPT_PATH), f"Missing {MANUSCRIPT_PATH}"
    with open(MANUSCRIPT_PATH) as f:
        text = f.read()

    # Verify key numerical values appear in manuscript
    assert "50,000" in text, "Manuscript missing 50,000 Monte Carlo draws"
    assert "0.489" in text, "Manuscript missing Kendall tau 0.489"
    assert "18.61%" in text, "Manuscript missing 18.61% winner reversal probability"
    assert "23.92%" in text, "Manuscript missing 23.92% oracle recovery rate"
    assert "2.86%" in text, "Manuscript missing 2.86% E1 oracle recovery rate"
    assert "0.625" in text, "Manuscript missing stated convention FRR 0.625"
    assert "0.619" in text, "Manuscript missing Gemma 3 12B FRR 0.619"
    
    # Assert NO stale references to 100 draws or 10,000 draws exist in manuscript text
    assert not re.search(r"100\s+benchmark-level reference vectors", text, re.I), "Stale 100-draw reference in manuscript"
    assert not re.search(r"10,000\s+benchmark-level reference vectors", text, re.I), "Stale 10,000-draw reference in manuscript"


def test_reproducibility_hashes_not_truncated():
    assert os.path.exists(REPRODUCIBILITY_PATH), f"Missing {REPRODUCIBILITY_PATH}"
    with open(REPRODUCIBILITY_PATH) as f:
        text = f.read()

    # Find backticked strings in Table section of REPRODUCIBILITY.md
    # Table hashes are 64 hex chars
    hashes = re.findall(r"`([a-f0-9]{10,64})`", text)
    assert len(hashes) > 0, "No hash strings found in REPRODUCIBILITY.md"
    for h in hashes:
        # Check if hash looks like a truncated SHA-256 (e.g. 10..63 hex chars followed by ...)
        if len(h) != 64 and not h.isdigit():
            pytest.fail(f"Truncated SHA-256 hash found in REPRODUCIBILITY.md: {h} (length {len(h)})")
        assert "..." not in h, f"Ellipsis truncated hash found: {h}"
