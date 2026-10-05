"""
Tests for RCR metrics, ranking calculations, Kendall tau, and oracle recovery.
"""

from research.ssr_pilot.rcrc.ranking_metrics import compute_kendall_tau, compute_model_scores, get_model_ranking


def test_ranking_metrics_and_kendall_tau():
    r1 = ["qwen3:8b", "gemma2:9b", "mistral:7b-instruct", "llama3.1:8b"]
    r2 = ["qwen3:8b", "gemma2:9b", "mistral:7b-instruct", "llama3.1:8b"]
    r3 = ["llama3.1:8b", "mistral:7b-instruct", "gemma2:9b", "qwen3:8b"]

    assert compute_kendall_tau(r1, r2) == 1.0
    assert compute_kendall_tau(r1, r3) == -1.0


def test_model_ranking_sorting():
    scores = {"m1": 0.5, "m2": 0.8, "m3": 0.2}
    ranking = get_model_ranking(scores)
    assert ranking == ["m2", "m1", "m3"]
