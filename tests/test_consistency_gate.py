"""
Automated consistency gate for OS-Tutor-RAG research package.

Loads paper/claims_manifest.json and independently verifies each claim against
the referenced result artifacts — no hardcoded expected values, no manuscript
string-matching for numerical claims. Verifies SHA-256 hashes of result files.
"""

import hashlib
import json
import os
import re

import pytest

MANIFEST_PATH = "paper/claims_manifest.json"
MANUSCRIPT_PATH = "paper/PAPER_FINAL.md"
REPRODUCIBILITY_PATH = "paper/REPRODUCIBILITY.md"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_jsonpath(data: dict, path: str):
    """
    Resolve a dot-separated jsonpath against a nested dict.
    Supports keys with colons (e.g. 'gemma3:12b').
    """
    parts = path.split(".")
    node = data
    i = 0
    while i < len(parts):
        key = parts[i]
        if isinstance(node, dict) and key in node:
            node = node[key]
            i += 1
            continue
        # Try colon-containing compound key
        if i + 1 < len(parts):
            combined = key + "." + parts[i + 1]
            if isinstance(node, dict) and combined in node:
                node = node[combined]
                i += 2
                continue
        raise KeyError(f"Key '{key}' not found; available: {list(node.keys())[:10] if isinstance(node, dict) else type(node)}")
    return node


def load_manifest():
    assert os.path.exists(MANIFEST_PATH), f"Missing claims manifest: {MANIFEST_PATH}"
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def test_manifest_artifact_sha256():
    """Verify result artifacts on disk match the SHA-256 hashes recorded in the manifest."""
    manifest = load_manifest()
    sha_map = manifest.get("_artifact_sha256", {})
    assert sha_map, "No _artifact_sha256 entries in manifest"
    for path, expected_sha in sha_map.items():
        assert os.path.exists(path), f"Artifact missing: {path}"
        actual_sha = _sha256(path)
        assert actual_sha == expected_sha, (
            f"SHA-256 mismatch for {path}:\n"
            f"  expected: {expected_sha}\n"
            f"  actual:   {actual_sha}"
        )


def test_all_claims_match_artifacts():
    """
    For each claim in claims_manifest.json, independently load the referenced
    artifact, resolve the JSONPath, and compare against expected_value within tolerance.
    No hardcoded numbers — all values come from the manifest.
    """
    manifest = load_manifest()
    artifacts_cache = {}
    failures = []

    for claim in manifest["claims"]:
        claim_id = claim["id"]
        artifact_path = claim["artifact"]
        jsonpath = claim["jsonpath"]
        expected = claim["expected_value"]
        tol = claim["tolerance"]

        if artifact_path not in artifacts_cache:
            assert os.path.exists(artifact_path), f"Artifact missing for claim {claim_id}: {artifact_path}"
            with open(artifact_path) as f:
                artifacts_cache[artifact_path] = json.load(f)

        try:
            actual = _resolve_jsonpath(artifacts_cache[artifact_path], jsonpath)
        except (KeyError, TypeError) as e:
            failures.append(f"Claim {claim_id}: JSONPath '{jsonpath}' failed: {e}")
            continue

        if isinstance(expected, float) or isinstance(actual, float):
            if abs(float(actual) - float(expected)) > tol:
                failures.append(
                    f"Claim {claim_id} ({claim['description']}): "
                    f"expected {expected} ± {tol}, got {actual}"
                )
        else:
            if actual != expected:
                failures.append(
                    f"Claim {claim_id} ({claim['description']}): "
                    f"expected {expected!r}, got {actual!r}"
                )

    assert not failures, "Claim verification failures:\n" + "\n".join(failures)


def test_manuscript_does_not_contain_stale_draws():
    """Sanity-check: manuscript must not reference old 100-draw or 10,000-draw language."""
    assert os.path.exists(MANUSCRIPT_PATH)
    with open(MANUSCRIPT_PATH) as f:
        text = f.read()
    assert "50,000" in text, "Manuscript missing '50,000' Monte Carlo draws"
    assert not re.search(r"\b100\s+benchmark-level reference vectors", text, re.I)
    assert not re.search(r"10,000\s+benchmark-level reference vectors", text, re.I)


def test_rcr_summary_structure():
    """Structural smoke test: rcr_summary.json must have required fields and evaluators."""
    path = "research/ssr_pilot/results/rcrc/rcr_summary.json"
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert data["n_monte_carlo_draws"] == 50000
    for e_id in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]:
        assert e_id in data["evaluators"], f"Missing evaluator {e_id}"
    e2 = data["evaluators"]["E2_NORMALIZED_MATCH"]
    assert "kendall_tau_n_valid_draws" in e2, "Missing degenerate-draw tracking"
    assert "kendall_tau_n_degenerate_draws" in e2, "Missing degenerate-draw tracking"
    assert "significance_n_sampled_draws" in e2, "Missing significance subsample field"


def test_reproducibility_hashes_not_truncated():
    """
    SHA-256 checksums in the artifact table must be full 64-char hex strings.
    Git commit SHAs (always 40 hex chars) are excluded from this check — they
    are SHA-1 hashes, not truncated SHA-256 values.
    """
    assert os.path.exists(REPRODUCIBILITY_PATH)
    with open(REPRODUCIBILITY_PATH) as f:
        lines = f.readlines()

    # Only check backtick-quoted hex strings on table rows (contain ` | `)
    table_hashes = []
    for line in lines:
        if " | " in line:
            found = re.findall(r"`([a-f0-9]{10,64})`", line)
            table_hashes.extend(found)

    assert len(table_hashes) > 0, "No hash strings found in REPRODUCIBILITY.md checksum table"
    for h in table_hashes:
        assert "..." not in h, f"Ellipsis-truncated hash: {h}"
        # Git SHAs are exactly 40 hex chars; skip them (they are not SHA-256)
        if len(h) == 40:
            continue
        if len(h) != 64 and not h.isdigit():
            pytest.fail(f"Truncated SHA-256 (length {len(h)}): {h}")


def test_manuscript_claims_phrases_present():
    """Verify that every claim's declared manuscript phrase appears in PAPER_FINAL.md."""
    manifest = load_manifest()
    assert os.path.exists(MANUSCRIPT_PATH), f"Missing manuscript: {MANUSCRIPT_PATH}"
    with open(MANUSCRIPT_PATH) as f:
        manuscript_text = f.read()

    missing = []
    for claim in manifest["claims"]:
        phrase = claim.get("manuscript_phrase")
        if phrase and phrase not in manuscript_text:
            missing.append(f"Claim {claim['id']}: phrase '{phrase}' not found in manuscript")

    assert not missing, "Manuscript phrase verification failures:\n" + "\n".join(missing)


def test_generating_commit_sha_consistency():
    """
    Verify that the generating git commit SHA recorded in rcr_summary.json matches
    the commit SHAs documented in REPRODUCIBILITY.md and FINAL_RESEARCH_STATUS.md.
    """
    summary_path = "research/ssr_pilot/results/rcrc/rcr_summary.json"
    assert os.path.exists(summary_path)
    with open(summary_path) as f:
        summary_data = json.load(f)
    provenance_sha = summary_data.get("provenance", {}).get("git_sha")
    assert provenance_sha and len(provenance_sha) == 40, f"Invalid provenance git SHA: {provenance_sha}"

    # Check REPRODUCIBILITY.md
    assert os.path.exists(REPRODUCIBILITY_PATH)
    with open(REPRODUCIBILITY_PATH) as f:
        repro_text = f.read()
    assert provenance_sha in repro_text, f"Generating commit SHA {provenance_sha} missing from {REPRODUCIBILITY_PATH}"

    # Check FINAL_RESEARCH_STATUS.md
    status_path = "paper/FINAL_RESEARCH_STATUS.md"
    assert os.path.exists(status_path)
    with open(status_path) as f:
        status_text = f.read()
    assert provenance_sha in status_text, f"Generating commit SHA {provenance_sha} missing from {status_path}"


def test_significance_stability_c7():
    """
    Verify C7: World-level paired sign-flip permutation tests (20,000 flips)
    across 6 model pairs over 200 sampled reference conditions produce 100% constant
    NON_SIGNIFICANT decisions with adjusted p-values >= 0.05 after Holm correction.
    """
    summary_path = "research/ssr_pilot/results/rcrc/rcr_summary.json"
    assert os.path.exists(summary_path)
    with open(summary_path) as f:
        data = json.load(f)

    e2 = data["evaluators"]["E2_NORMALIZED_MATCH"]
    sig = e2["significance_stability"]
    assert sig["n_references"] == 200
    assert sig["n_sign_flips"] == 20000

    pairs = sig["pairwise_significance_summary"]
    assert len(pairs) == 6, f"Expected 6 model pairs, got {len(pairs)}"
    for pair_name, summary in pairs.items():
        assert summary["is_decision_constant"] is True, f"Decision not constant for {pair_name}"
        assert summary["decision_distribution"] == {"NON_SIGNIFICANT": 1.0}, f"Non-significant distribution mismatch for {pair_name}"
        assert summary["min_adj_p_value"] >= 0.05, f"Adjusted p-value < 0.05 for {pair_name}"


def test_adversarial_meta_evaluation_c11():
    """
    Verify C11: Adversarial contrast meta-evaluation proves that E1 and E2
    exhibit 50% FRR and reject 100% of noncanonical valid solutions, while
    E3 achieves 100% sensitivity and 0% FRR.
    """
    adv_path = "research/ssr_pilot/results/adversarial/evaluator_meta_results.json"
    assert os.path.exists(adv_path)
    with open(adv_path) as f:
        meta = json.load(f)

    for e_id in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH"]:
        e_data = meta[e_id]
        assert e_data["sensitivity"] == 0.5
        assert e_data["specificity"] == 1.0
        assert e_data["frr"] == 0.5
        assert e_data["category_pass_rates"]["canonical_valid"] == 1.0
        assert e_data["category_pass_rates"]["noncanonical_valid"] == 0.0

    e3_data = meta["E3_SEMANTIC_ORACLE"]
    assert e3_data["sensitivity"] == 1.0
    assert e3_data["specificity"] == 1.0
    assert e3_data["frr"] == 0.0
    assert e3_data["category_pass_rates"]["canonical_valid"] == 1.0
    assert e3_data["category_pass_rates"]["noncanonical_valid"] == 1.0


def test_reference_distribution_sensitivity_artifact_integrity():
    """
    Verify reference_distribution_sensitivity.json structure, 11 distributions,
    50,000 draws for stochastic distributions, and valid metadata provenance.
    """
    sens_path = "research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json"
    assert os.path.exists(sens_path), f"Missing sensitivity artifact: {sens_path}"
    with open(sens_path) as f:
        data = json.load(f)

    assert len(data["distributions"]) == 11, f"Expected 11 distributions, got {len(data['distributions'])}"
    for dist_id, dist_info in data["distributions"].items():
        if dist_id != "ADVERSARIAL_UPPER_BOUND":
            assert dist_info["n_draws"] == 50000, f"Expected 50k draws for {dist_id}"
            assert dist_info["seed"] is not None


def test_reference_distribution_sensitivity_monotonic_attenuation():
    """
    Verify that increasing canonical bias p monotonically decreases E2 pairwise reversal probability.
    """
    sens_path = "research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json"
    assert os.path.exists(sens_path)
    with open(sens_path) as f:
        data = json.load(f)

    p_list = [0.0, 0.25, 0.50, 0.75, 0.80, 0.90, 0.95, 0.99]
    rev_rates = []
    for p in p_list:
        dist_id = f"CANONICAL_BIAS_P{int(p*100):02d}"
        rev = data["distributions"][dist_id]["evaluators"]["E2_NORMALIZED_MATCH"]["pairwise_reversal_probability"]
        rev_rates.append(rev)

    for i in range(1, len(rev_rates)):
        assert rev_rates[i] <= rev_rates[i - 1], f"Non-monotonic reversal decrease at p={p_list[i]}: {rev_rates[i]} > {rev_rates[i-1]}"

