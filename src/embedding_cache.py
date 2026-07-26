"""Process-wide cache of loaded SentenceTransformer models, keyed by model name.

SentenceTransformer(name) reloads the model weights on every construction
(~5s for bge-large-en-v1.5) -- it does no caching of its own. Stages that
embed inside a per-call function rather than holding a model on an instance
(semantic chunking, called per document; MMR, called per query) would
otherwise pay that cost on every call, which dominates their runtime.
Retrievers that already load a model once in __init__ (e.g. DenseRetriever)
don't need this, though using it lets them share one instance when configured
with the same model name.

Models default to CPU (override with OS_RAG_EMBEDDING_DEVICE). The GPU here is
shared with Ollama, whose generation and judge models want most of an 8GB
card on their own. Measured on this machine: torch holding ~1.5GB of VRAM
pushed Ollama into CPU offload and made generation 5-13x slower (llama3 went
from 2.0s to 25.8s per call), and eventually OOMed outright. Since LLM calls
dominate a sweep's runtime while embedding is amortized by the caches above,
conceding the GPU to Ollama is the cheaper trade.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

_DEVICE = os.environ.get("OS_RAG_EMBEDDING_DEVICE", "cpu")

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder, SentenceTransformer

_MODEL_CACHE: dict[str, "SentenceTransformer"] = {}
_CROSS_ENCODER_CACHE: dict[str, "CrossEncoder"] = {}


def get_embedding_model(model_name: str) -> "SentenceTransformer":
    """Return a cached SentenceTransformer for `model_name`, loading it once.

    Args:
        model_name: HuggingFace model id (e.g. "BAAI/bge-large-en-v1.5").

    Returns:
        The shared SentenceTransformer instance for that model name.
    """
    if model_name not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer

        _MODEL_CACHE[model_name] = SentenceTransformer(model_name, device=_DEVICE)
    return _MODEL_CACHE[model_name]


def release_gpu_memory() -> None:
    """Move every cached model to CPU and free whatever VRAM they held.

    A no-op under the default CPU device, but kept for runs that opt into
    OS_RAG_EMBEDDING_DEVICE=cuda: it hands the card back before Ollama loads a
    model that needs most of it.
    """
    import torch

    if not torch.cuda.is_available():
        return

    for model in _MODEL_CACHE.values():
        model.to("cpu")

    for cross_encoder in _CROSS_ENCODER_CACHE.values():
        # CrossEncoder.predict() re-issues `self.model.to(self._target_device)`
        # on every call, so moving the module alone is undone at the next
        # rerank -- the reranker would pull itself back onto the GPU while
        # Ollama holds it, which is exactly the contention this releases.
        cross_encoder._target_device = torch.device("cpu")
        cross_encoder.model.to("cpu")

    torch.cuda.empty_cache()


def get_cross_encoder(model_name: str) -> "CrossEncoder":
    """Return a cached CrossEncoder for `model_name`, loading it once.

    Same rationale as get_embedding_model: a mass eval sweep constructs one
    reranker per config variant, and reloading the cross-encoder each time
    dominates that stage's cost.

    Args:
        model_name: HuggingFace model id (e.g. "BAAI/bge-reranker-large").

    Returns:
        The shared CrossEncoder instance for that model name.
    """
    if model_name not in _CROSS_ENCODER_CACHE:
        from sentence_transformers import CrossEncoder

        _CROSS_ENCODER_CACHE[model_name] = CrossEncoder(model_name, device=_DEVICE)
    return _CROSS_ENCODER_CACHE[model_name]
