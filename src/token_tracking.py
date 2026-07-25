"""LLM call/token accounting, used to report per-run cost estimates in the
eval workbook (see evaluation.append_run_to_workbook).

Every call is tokenized with OpenAI's o200k_base encoding (used by both
GPT-4.1 and GPT-4o-mini) rather than the local model's own tokenizer -- the
counts feed a "what would this have cost on OpenAI's API" estimate, so
tokenizing with the target API's own encoder is what makes that estimate
meaningful, even though the actual call ran against a local Ollama model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import tiktoken

_ENCODING = tiktoken.get_encoding("o200k_base")

# USD per 1M tokens. Verify against OpenAI's current pricing page before
# treating these as authoritative -- API pricing changes over time and these
# are a snapshot, not a live lookup.
PRICING_PER_MILLION_TOKENS = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def count_tokens(text: str) -> int:
    """Approximate token count for `text` using the GPT-4.1/4o-mini encoder."""
    return len(_ENCODING.encode(text))


def estimate_cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    """Estimate USD cost for a token count as if billed under `model`'s pricing.

    Args:
        input_tokens: Total input (prompt) tokens.
        output_tokens: Total output (completion) tokens.
        model: One of PRICING_PER_MILLION_TOKENS's keys (e.g. "gpt-4.1").

    Returns:
        Estimated cost in USD.
    """
    rates = PRICING_PER_MILLION_TOKENS[model]
    return (input_tokens / 1_000_000) * rates["input"] + (output_tokens / 1_000_000) * rates["output"]


@dataclass
class LLMCallTracker:
    """Records every LLM call made during a pipeline run or eval pass."""

    calls: list[dict] = field(default_factory=list)

    def record(self, purpose: str, prompt: str, response: str) -> None:
        """Log one LLM call's token usage.

        Args:
            purpose: Short label for what the call was for (e.g.
                "generate_answer", "hyde_hypothetical",
                "multi_query_variants", "llm_rerank_score", "ragas_judge").
            prompt: The full input text sent to the model.
            response: The model's output text.
        """
        self.calls.append(
            {
                "purpose": purpose,
                "input_tokens": count_tokens(prompt),
                "output_tokens": count_tokens(response),
            }
        )

    @property
    def num_calls(self) -> int:
        return len(self.calls)

    @property
    def total_input_tokens(self) -> int:
        return sum(c["input_tokens"] for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c["output_tokens"] for c in self.calls)

    def calls_by_purpose(self) -> dict[str, int]:
        """Count of calls grouped by purpose label."""
        counts: dict[str, int] = {}
        for c in self.calls:
            counts[c["purpose"]] = counts.get(c["purpose"], 0) + 1
        return counts
