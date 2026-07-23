"""Central configuration for the RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PathConfig:
    """Filesystem locations used across the pipeline."""

    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")
    index_dir: Path = Path("data/index")


@dataclass
class ChunkingConfig:
    """Parameters controlling chunking strategies.

    ``strategy_by_source_type`` selects which strategy runs for a given
    ``Document.metadata["source_type"]`` (e.g. "pptx", "docx", "text"),
    falling back to ``default_strategy`` when the source type is absent or
    unmapped. Valid strategy names are "structure_aware" and "semantic".
    """

    default_strategy: str = "structure_aware"
    strategy_by_source_type: dict[str, str] = field(
        default_factory=lambda: {
            "pptx": "structure_aware",
            "docx": "structure_aware",
            "text": "semantic",
        }
    )
    chunk_size: int = 512
    chunk_overlap: int = 64
    semantic_similarity_threshold: float = 0.6
    semantic_embedding_model_name: str = "BAAI/bge-small-en-v1.5"


@dataclass
class RetrievalConfig:
    """Parameters controlling retrieval techniques.

    ``technique`` selects which retriever the pipeline builds: "dense",
    "bm25", "hybrid_rrf", or "hyde".
    """

    technique: str = "hybrid_rrf"
    dense_model_name: str = "BAAI/bge-large-en-v1.5"
    top_k: int = 10
    rrf_k: int = 60
    index_dir: Path = Path("data/index")


@dataclass
class RerankingConfig:
    """Parameters controlling reranking techniques.

    ``method`` selects which reranker the pipeline applies: "cross_encoder",
    "llm_rerank", or "none" to skip reranking entirely.
    """

    method: str = "cross_encoder"
    cross_encoder_model_name: str = "BAAI/bge-reranker-large"
    top_n: int = 5


@dataclass
class DiversificationConfig:
    """Parameters controlling result diversification (e.g. MMR)."""

    enabled: bool = True
    lambda_param: float = 0.5
    top_k: int = 5
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"


@dataclass
class GenerationConfig:
    """Parameters controlling the local LLM generation backend.

    Defaults to the "ollama" backend against a locally running llama3:latest
    model, since the real Llama-3.1-8B-Instruct/vLLM deploy target doesn't
    fit this dev machine's 8GB VRAM without quantization (see DELAYED_TASKS.md).
    Swap ``model_name`` to "gemma2:9b" once pulled, or ``backend`` to "vllm"
    for the real deploy target.
    """

    model_name: str = "llama3:latest"
    backend: str = "ollama"
    max_tokens: int = 512
    temperature: float = 0.2
    gpu_memory_utilization: float = 0.85
    # Used when backend == "ollama" (local dev/testing against an Ollama server).
    ollama_base_url: str = "http://localhost:11434"


@dataclass
class PipelineConfig:
    """Top-level configuration aggregating all pipeline stages."""

    paths: PathConfig = field(default_factory=PathConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    reranking: RerankingConfig = field(default_factory=RerankingConfig)
    diversification: DiversificationConfig = field(default_factory=DiversificationConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
