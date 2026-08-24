"""One-shot misconception detection for the teaching-mode chat prompt.

Deliberately import-independent of ``src.generation.local_llm`` (per spec):
this module makes its own blocking (stream=false) call to Ollama's
``/api/generate``, replicating the request shape LocalLLM._complete /
score_relevance use, rather than instantiating a LocalLLM.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger("api.chat.misconception")

_MISCONCEPTION_PROMPT_TEMPLATE = (
    "You are analyzing a student's question from an operating systems course "
    "to see if its phrasing suggests a specific wrong mental model (a "
    "misconception), not just an information gap.\n\n"
    "Some example confusions common in this material:\n"
    "- Deadlock vs. starvation: deadlock is a cycle of processes each waiting "
    "on a resource held by another, permanently blocked; starvation is a "
    "process perpetually losing a scheduling race for a resource it could in "
    "principle get. A question that assumes preventing one prevents the "
    "other reflects this confusion.\n"
    "- Paging vs. segmentation: paging divides memory into fixed-size frames "
    "invisible to the programmer; segmentation divides it into "
    "variable-size, logically meaningful units. A question that treats them "
    "as the same mechanism reflects this confusion.\n"
    "- Process vs. thread: a process has its own address space; threads "
    "within a process share one address space. A question that assumes "
    "threads have separate memory like processes reflects this confusion.\n"
    "- Mutex vs. semaphore: a mutex is a binary lock owned by the thread "
    "that acquired it; a semaphore is a counter usable for signaling between "
    "threads with no ownership. A question that uses them interchangeably "
    "reflects this confusion.\n\n"
    "Question: {question}\n\n"
    "If the question's phrasing suggests one specific wrong mental model, "
    "respond with a short label, a colon, and a one-sentence description of "
    "the suspected misconception (e.g. \"deadlock-vs-starvation: the "
    "question conflates deadlock avoidance with preventing starvation.\"). "
    "If it does not suggest any specific misconception, respond with exactly "
    "the single word: none\n\n"
    "Response:"
)


def check_misconception(
    question: str,
    ollama_base_url: str,
    model_name: str,
    temperature: float = 0.0,
) -> str:
    """Classify whether a question's phrasing suggests a specific wrong mental model.

    Makes one blocking (non-streaming) call to Ollama's /api/generate.

    Args:
        question: The student's question text.
        ollama_base_url: Base URL of the running Ollama server.
        model_name: Ollama model to use for the classification call.
        temperature: Sampling temperature for the classification call.

    Returns:
        A short "label: description" string naming the suspected
        misconception, or "" if none was detected or the response couldn't
        be parsed. Callers should treat "" as the common case, not an error.
    """
    prompt = _MISCONCEPTION_PROMPT_TEMPLATE.format(question=question)

    try:
        response = requests.post(
            f"{ollama_base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=60,
        )
        response.raise_for_status()
        text = response.json()["response"].strip()
    except Exception:
        logger.exception("Misconception check call failed; treating as none")
        return ""

    if not text:
        return ""

    normalized = text.strip().strip(".").lower()
    if normalized == "none" or normalized.startswith("none"):
        return ""

    # Guard against a verbose/unparseable response that doesn't follow the
    # "label: description" shape but also isn't a clean "none" -- still
    # usable as a free-text note, just cap it defensively.
    return text.strip()[:500]
