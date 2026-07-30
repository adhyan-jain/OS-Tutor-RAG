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
    ``Document.metadata["source_type"]``, falling back to ``default_strategy``
    when the source type is absent or unmapped. Valid strategy names are
    "structure_aware", "page_aware" and "semantic".

    Each source type is matched to the strategy that fits how that format is
    actually written, rather than being treated as a tunable axis:

    - pptx: "structure_aware" -- decks carry their meaning in slide structure,
      so children are title-qualified bullets and the slide is the parent.
    - pdf: "page_aware" -- textbook pages are continuous prose, so children are
      semantic passages bounded by the page, and the page is the parent.
    - docx: "structure_aware" -- headed sections chunk into overlapping windows
      with the section as parent.
    - text: "semantic" -- no structure to exploit, so fall back to topic shifts.
    """

    default_strategy: str = "semantic"
    strategy_by_source_type: dict[str, str] = field(
        default_factory=lambda: {
            "pptx": "structure_aware",
            "docx": "structure_aware",
            "pdf": "page_aware",
            "text": "semantic",
        }
    )
    chunk_size: int = 512
    chunk_overlap: int = 64
    semantic_similarity_threshold: float = 0.6
    semantic_embedding_model_name: str = "BAAI/bge-large-en-v1.5"


@dataclass
class RetrievalConfig:
    """Parameters controlling retrieval techniques.

    ``technique`` selects which base retriever the pipeline builds: "dense",
    "bm25", "hybrid_rrf", or "hyde".

    ``use_multi_query`` is orthogonal to ``technique``: when True, the chosen
    base retriever is wrapped so the query is fanned out into several
    LLM-reformulated variants, each retrieved independently and fused via RRF
    (reusing the same fusion as "hybrid_rrf") -- regardless of which technique
    it wraps, including "hyde". Pairing it with HyDE drafts a hypothetical
    answer per variant, which is nearer the originally published HyDE (it
    samples several hypothetical documents) than the single-shot version here.
    """

    # Defaults follow what measured best rather than what is conventional:
    # dense alone beat hybrid_rrf on recall@5 (0.923 against 0.846), because
    # reciprocal rank fusion gives BM25's rankings equal weight and BM25 fails
    # to surface the right slide half the time on this corpus.
    technique: str = "dense"
    dense_model_name: str = "BAAI/bge-large-en-v1.5"
    top_k: int = 10
    # How much wider than the narrowest downstream stage to retrieve when
    # reranking and/or diversification will filter the results. A selection
    # stage can only select if it is handed more candidates than it keeps:
    # retrieving top_k=10, reranking to 5 and then asking MMR for 5 leaves MMR
    # choosing 5 from 5, i.e. reordering rather than diversifying. Widening the
    # pool costs retrieval and reranking compute but no extra LLM calls, since
    # generation and the RAGAS metrics only ever see the final selection.
    #
    # Widening cannot rescue a stage that is harmful in kind rather than in
    # degree. MMR measured -0.038 on hit@8 because its objective trades
    # relevance for diversity this corpus does not need, and a larger pool
    # offers it more ways to make that trade, not fewer. Both stages are
    # therefore off by default (see RerankingConfig.method and
    # DiversificationConfig.enabled); the multiplier governs their behaviour
    # only when a sweep deliberately turns them back on.
    candidate_pool_multiplier: int = 3
    # Most chunks any single slide or page may contribute to the candidate
    # pool; 0 disables the cap, which is the default because it measured no
    # benefit here.
    #
    # Sibling crowding is real -- only 68% of top-5 slots held distinct
    # parents, and one slide once took 9 of the top 10 -- and capping does fix
    # it, raising distinct contexts from 3.5 to 5.0. But hit rate was unchanged
    # to three decimals at every cap, because MMR already selects for
    # dissimilarity and was discarding most siblings anyway. Simply raising the
    # final context count beat capping on both axes (k=10 uncapped: hit 1.000
    # at 922 tokens; k=8 capped at 1: hit 0.962 at 1006 tokens). Retained
    # because it may pay off on a corpus with no diversification stage.
    max_chunks_per_parent: int = 0
    rrf_k: int = 60
    index_dir: Path = Path("data/index")
    use_multi_query: bool = False
    # Used when use_multi_query is True. Five, not three: measured recall@5
    # 1.000 and full_recall 0.577 at five against 0.962 and 0.538 at three,
    # and seven is worse than five on both -- by the seventh reformulation the
    # variants drift far enough from the question to retrieve off-topic
    # passages, which RRF then weights equally.
    num_query_variants: int = 5


@dataclass
class RerankingConfig:
    """Parameters controlling reranking techniques.

    ``method`` selects which reranker the pipeline applies: "cross_encoder",
    "llm_rerank", or "none" to skip reranking entirely.
    """

    # Off by default: the cross-encoder measured ~0.05 *worse* on
    # answer_correctness than omitting it, consistently and in both MMR
    # settings. Dense retrieval already reaches recall@5 of 0.923, so the
    # reranker reorders an already-good ranking, and bge-reranker-large is
    # general-purpose with no advantage on this material.
    method: str = "none"
    cross_encoder_model_name: str = "BAAI/bge-reranker-large"
    top_n: int = 8


@dataclass
class ContextExpansionConfig:
    """Whether generation reads retrieved child chunks or their parent units.

    structure_aware chunking emits deliberately tiny children (one slide bullet
    or title) and records the containing slide/section on each as
    ``parent_text``. Retrieving precise children but generating from their
    parents is the point of that design -- without this step the LLM sees only
    the ~50-character child and frequently answers that its context contains no
    answer. No effect on chunks lacking a parent (semantic chunking).

    ``max_parent_tokens`` bounds how much a single parent may contribute, and
    matters because parents are not uniformly sized. Measured on this corpus:
    a slide parent is ~72 tokens (5x its child) while a PDF page parent is
    ~534 tokens and can reach 913 (11x its child). Expanding slides is
    therefore nearly free, but expanding pages inflated context from 149 to
    1137 tokens per question -- paid for repeatedly, since the context is
    re-sent in the generation prompt and in most judge calls. Oversized
    parents are windowed around the matched child instead of being dropped, so
    the passage keeps its immediate surroundings without carrying a whole page.
    """

    enabled: bool = True
    max_parent_tokens: int = 250


@dataclass
class DiversificationConfig:
    """Parameters controlling result diversification (e.g. MMR)."""

    # Off by default: MMR measured -0.038 on hit@8 and -0.038 on full_hit@10,
    # dropping correct slides in exchange for diversity this corpus does not
    # need. top_k is the number of contexts generation receives; 8 without MMR
    # reaches a hit rate of 1.000, where 5 reached only 0.885.
    enabled: bool = False
    lambda_param: float = 0.5
    top_k: int = 8
    embedding_model_name: str = "BAAI/bge-large-en-v1.5"


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
    # Which answer prompt to use (see local_llm._RAG_PROMPT_TEMPLATES).
    #
    # "few_shot" by measurement: against "strict" on the same config it raised
    # answer_correctness from 0.664 to 0.756 and faithfulness from 0.942 to
    # 0.986. For scale, the whole eight-variant retrieval sweep spanned 0.052,
    # so aligning the shape of the answer mattered more than any technique
    # choice -- consistent with answers losing points to statement granularity
    # rather than to content.
    #
    # "cot" also measured worse (answer_correctness 0.748 -> 0.689, faithfulness
    # 0.981 -> 0.933; FINDINGS A19). Reasoning before the answer shortened the
    # answer by 27%, and since answer_correctness compares statement sets, the
    # dropped statements are lost recall. Kept as a recorded negative.
    #
    # "part_coverage" measured actively harmful (faithfulness 0.819) and is
    # kept only as a recorded negative: inviting partial answers reads as
    # licence to fill the gaps from the model's own knowledge.
    prompt_style: str = "few_shot"


@dataclass
class EvalConfig:
    """Parameters controlling the pipeline's automatic per-run RAGAS evaluation.

    After ``RAGPipeline.ingest()``, ``RAGPipeline.evaluate()`` scores the
    pipeline against the first ``num_questions`` examples in
    ``eval_set_path``, appending the results as a new sheet in
    ``output_workbook_path`` (plus updating its "Final Analysis" sheet).
    Set ``num_questions`` to change how many questions to analyze without
    touching any code.
    """

    eval_set_path: Path = Path("eval/eval_set.json")
    num_questions: int = 10
    output_workbook_path: Path = Path("eval/pipeline_runs.xlsx")
    # Deliberately a different model than GenerationConfig.model_name: using
    # the same model to both answer and grade its own answers is a known
    # self-preference bias in LLM-as-judge setups. Assumed reachable at the
    # same ollama_base_url as generation.
    #
    # qwen2.5 (not gemma2:9b) because judging dominates a sweep's runtime --
    # ~18 of the ~19 LLM calls per question are judge calls. A 7B model that
    # fits entirely in this machine's 8GB VRAM measured ~2x faster per call
    # than a 9B one that partially offloads to CPU.
    judge_model_name: str = "qwen2.5:7b"


@dataclass
class PipelineConfig:
    """Top-level configuration aggregating all pipeline stages."""

    paths: PathConfig = field(default_factory=PathConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    reranking: RerankingConfig = field(default_factory=RerankingConfig)
    diversification: DiversificationConfig = field(default_factory=DiversificationConfig)
    context_expansion: ContextExpansionConfig = field(default_factory=ContextExpansionConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
