/**
 * Every number on the /research page lives here, next to the repo file it was
 * copied from. Nothing is computed or rounded beyond what the source states.
 */

export interface Sourced {
  /** Where the figure comes from: a finding id and/or a repo path. */
  src: string;
}

// ---------------------------------------------------------------- effect sizes
// FINDINGS.md A20 table: change in answer_correctness vs the ~0.027 noise floor.
export const NOISE_FLOOR = 0.027; // FINDINGS.md A20 (0.7752 vs 0.7478 on one identical config)

export interface Effect extends Sourced {
  label: string;
  delta: number;
  established: boolean;
  note: string;
}

export const EFFECTS: Effect[] = [
  { label: "Defect fixes (F-series)", delta: 0.111, established: true, note: "4x noise", src: "FINDINGS A20" },
  { label: "strict → few_shot prompt", delta: 0.092, established: true, note: "3x noise", src: "FINDINGS A17, A20" },
  { label: "few_shot → chain-of-thought", delta: -0.059, established: true, note: "2x noise, mechanism confirmed", src: "FINDINGS A19, A20" },
  { label: "cross-encoder reranking", delta: 0.029, established: false, note: "about 1x noise", src: "FINDINGS A16, A20" },
  { label: "multi-query", delta: 0.014, established: false, note: "below noise", src: "FINDINGS A16, A20" },
  { label: "temperature 0.2 → 0.0", delta: -0.013, established: false, note: "below noise", src: "FINDINGS A20" },
];

// ------------------------------------------------------- retrieval (A12 table)
export const RETRIEVAL_COLS = ["R@1", "R@3", "R@5", "R@10", "full@5", "MRR"] as const;
export const RETRIEVAL_ROWS: { name: string; values: number[] }[] = [
  { name: "dense", values: [0.769, 0.962, 1.0, 1.0, 0.577, 0.875] },
  { name: "hyde", values: [0.654, 0.923, 1.0, 1.0, 0.692, 0.804] },
  { name: "dense + multi_query", values: [0.808, 0.923, 0.962, 1.0, 0.577, 0.873] },
  { name: "hybrid_rrf + multi_query", values: [0.769, 0.885, 0.962, 0.962, 0.654, 0.848] },
  { name: "hybrid_rrf", values: [0.769, 0.808, 0.923, 1.0, 0.538, 0.826] },
  { name: "bm25", values: [0.654, 0.731, 0.885, 0.923, 0.462, 0.736] },
];
export const RETRIEVAL_SRC = "FINDINGS A12 · eval/retrieval_eval.py · 26 questions, 22-document corpus";

// ---------------------------------------------------------- 8-variant sweep A16
export interface Variant extends Sourced {
  name: string;
  composite: number;
  ansCorr: number;
  faith: number;
  calls: number;
  cost: string;
}
export const SWEEP_A16: Variant[] = [
  { name: "dense + multi_query", composite: 0.772, ansCorr: 0.662, faith: 0.958, calls: 480, cost: "$0.160", src: "A16" },
  { name: "hyde + cross_encoder", composite: 0.764, ansCorr: 0.644, faith: 0.958, calls: 491, cost: "$0.195", src: "A16" },
  { name: "hyde", composite: 0.752, ansCorr: 0.631, faith: 0.929, calls: 510, cost: "$0.227", src: "A16" },
  { name: "dense + cross_encoder", composite: 0.744, ansCorr: 0.642, faith: 0.949, calls: 448, cost: "$0.153", src: "A16" },
  { name: "hyde + multi_query + cross_encoder", composite: 0.743, ansCorr: 0.656, faith: 0.882, calls: 593, cost: "$0.282", src: "A16" },
  { name: "dense", composite: 0.74, ansCorr: 0.629, faith: 0.899, calls: 451, cost: "$0.148", src: "A16" },
  { name: "hyde + multi_query", composite: 0.734, ansCorr: 0.637, faith: 0.912, calls: 615, cost: "$0.296", src: "A16" },
  { name: "dense + multi_query + cross_encoder", composite: 0.72, ansCorr: 0.607, faith: 0.883, calls: 471, cost: "$0.163", src: "A16" },
];

// Later focused sweep (few_shot prompt), eval/comparison_results.md
export const SWEEP_POSTFIX: { name: string; ansCorr: number; faith: number }[] = [
  { name: "dense + multi_query + cross_encoder", ansCorr: 0.7752, faith: 1.0 },
  { name: "hyde + cross_encoder", ansCorr: 0.7697, faith: 0.9717 },
  { name: "dense + cross_encoder", ansCorr: 0.7611, faith: 0.9712 },
  { name: "hyde + multi_query + cross_encoder", ansCorr: 0.7503, faith: 0.9817 },
  { name: "dense + multi_query", ansCorr: 0.7462, faith: 0.9776 },
  { name: "hyde + multi_query", ansCorr: 0.7412, faith: 0.956 },
  { name: "dense", ansCorr: 0.7303, faith: 0.9776 },
  { name: "hyde", ansCorr: 0.7082, faith: 0.9519 },
];

// -------------------------------------------------------------- prompts A17/A19
export const PROMPTS_A17 = [
  { name: "strict (old default)", ansCorr: 0.664, faith: 0.942 },
  { name: "few_shot (adopted)", ansCorr: 0.756, faith: 0.986 },
  { name: "part_coverage", ansCorr: 0.631, faith: 0.819 },
];
export const PROMPTS_A19 = [
  { name: "few_shot", ansCorr: 0.7478, faith: 0.9808, words: 35.6 },
  { name: "cot (reasoning first)", ansCorr: 0.6887, faith: 0.9333, words: 26.0 },
];

// ------------------------------------------------- faithfulness vs refusal (A1)
export const REFUSAL_ROWS = [
  { name: "hyde", refusal: 5.0, faith: 0.883, ansCorr: 0.707 },
  { name: "dense", refusal: 3.8, faith: 0.813, ansCorr: 0.616 },
  { name: "hybrid_rrf", refusal: 12.5, faith: 0.872, ansCorr: 0.649 },
  { name: "bm25", refusal: 11.7, faith: 0.828, ansCorr: 0.509 },
];

// -------------------------------------------------- defects that looked like results
export const DEFECTS = [
  { id: "F1", title: "Slide titles indexed as standalone chunks", effect: "BM25 looked far worse than dense; real cause was question-shaped title chunks. Bare question chunks 12 → 0." },
  { id: "F2", title: "parent_text recorded but never read", effect: "Model said \"context has no answer\" while retrieval had the right slide. Fixed by parent expansion; refusals 11.7% → ~0%." },
  { id: "F13", title: "Selection stages had nothing to select from", effect: "Retrieve 10 → rerank 5 → MMR 5 can only reorder. Earlier MMR and reranking conclusions were discarded." },
  { id: "A11", title: "The benchmark was biased against lexical retrieval", effect: "BM25 recall@5 rose 0.500 → 0.885 with no retriever change, only a rebuilt question set." },
  { id: "F15", title: "PPTX tables never indexed", effect: "+20.1% slide text recovered. No score moved: no question asked about it (A18)." },
  { id: "F9/F10", title: "torch and Ollama fighting over one 8 GB GPU", effect: "llama3 2.0 s/call with a free GPU vs 25.8 s under contention (13x)." },
];

// -------------------------------------------------------------- refuted claims
export const REFUTED = [
  { id: "A3", claim: "Verbose, hedging answers depress correctness", measured: "Longest third of answers scored higher (0.696 vs 0.659)." },
  { id: "A6", claim: "Whole-slide chunks retrieve better than bullets", measured: "Dense R@5 fell 0.923 → 0.577." },
  { id: "A9", claim: "Capping siblings per slide improves retrieval", measured: "Distinct contexts 3.5 → 5.0, hit rate unchanged to three decimals." },
  { id: "A10", claim: "MMR diversification helps", measured: "hit@8 1.000 → 0.962 with MMR on." },
  { id: "A13", claim: "HyDE's retrieval breadth reaches the answer", measured: "answer_correctness +0.002, context_entity_recall 0.488 vs 0.491." },
  { id: "H2", claim: "HyDE and multi-query stack", measured: "Combined 0.734 composite, below both parents (0.752, 0.772)." },
  { id: "H4", claim: "Part-coverage prompting converts partial retrieval into partial credit", measured: "Faithfulness 0.942 → 0.819." },
  { id: "H12", claim: "Chain-of-thought beats few-shot", measured: "answer_correctness 0.748 → 0.689; lost 14 of 26 questions." },
  { id: "H11", claim: "Temperature changes correctness", measured: "−0.013, inside the 0.027 noise floor. Adopted for reproducibility only." },
];

// ------------------------------------------------------------------- metrics
export interface Metric {
  name: string;
  side: "retrieval" | "generation";
  sees: string;
  how: string;
  calls: string;
}
export const METRICS: Metric[] = [
  { name: "context_precision", side: "retrieval", sees: "question, each context, ground truth", how: "Judge says 1/0 per context (useful for the ground-truth answer?). Score = average precision over the context order, so relevant contexts ranked first score higher.", calls: "1 per context" },
  { name: "context_recall", side: "retrieval", sees: "question, all contexts joined, ground truth", how: "Judge splits the ground truth into statements and marks each attributable to the context (1) or not (0). Score = attributed / total.", calls: "1" },
  { name: "context_entity_recall", side: "retrieval", sees: "ground truth, all contexts joined", how: "Judge extracts entities from each text. Score = |entities in both| / |ground-truth entities|, a string-set intersection (unreliable here, A15).", calls: "2" },
  { name: "faithfulness", side: "generation", sees: "question, answer, contexts", how: "Judge decomposes the answer into statements, then marks each as inferable from the context or not. Score = supported / total. A refusal makes no claims, so it scores 1.0.", calls: "2" },
  { name: "answer_relevancy", side: "generation", sees: "answer (and question for the cosine)", how: "Judge writes 3 questions the answer would address. Score = mean cosine(question, generated) from bge-small embeddings, times 0 if any is flagged noncommittal.", calls: "3 (n=3)" },
  { name: "answer_similarity", side: "generation", sees: "answer, ground truth", how: "Cosine similarity of bge-small embeddings. No judge call.", calls: "0" },
  { name: "answer_correctness", side: "generation", sees: "question, answer, ground truth", how: "Both texts become statements; judge labels TP/FP/FN. Score = 0.75 × F1 + 0.25 × answer_similarity, with F1 = TP / (TP + ½(FP + FN)).", calls: "3" },
];

export const STAGE_INPUTS = [
  { stage: "Ingest", input: "data/raw/ PPTX, PDF, DOCX files", output: "Document objects (slides, pages, sections)" },
  { stage: "Chunk", input: "Document + per-format strategy", output: "Small child chunks, each carrying its slide or page as parent_text" },
  { stage: "Index", input: "Child chunk texts", output: "bge-large embeddings in a FAISS flat inner-product index" },
  { stage: "Query transform (optional)", input: "The student question", output: "multi_query: question + 5 LLM rewrites; hyde: one hypothetical answer" },
  { stage: "Retrieve", input: "Query text(s)", output: "Top-k child chunks by cosine; multi-query lists fused with RRF (k = 60)" },
  { stage: "Rerank (optional)", input: "(question, chunk) pairs", output: "bge-reranker-large order, top 8" },
  { stage: "Expand", input: "Selected children", output: "Parent slide/page, de-duplicated, capped at 400 tokens (windowed around the match)" },
  { stage: "Generate", input: "Filled prompt: instruction + 2 worked examples + contexts + question", output: "Answer from llama3 at temperature 0" },
  { stage: "Judge", input: "{question, answer, contexts, ground_truth}", output: "Seven metric scores per question from qwen2.5:7b" },
];

// ------------------------------------------------------------------------ RCR
// research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.csv
export const RCR_SENSITIVITY = [
  { label: "uniform", value: 17.23 },
  { label: "p = 0.25", value: 14.6 },
  { label: "p = 0.50", value: 12.14 },
  { label: "p = 0.75", value: 8.4 },
  { label: "p = 0.90", value: 4.33 },
  { label: "p = 0.95", value: 2.3 },
  { label: "p = 0.99", value: 0.47 },
];
// research/ssr_pilot/results/rcrc/kref_attenuation.json (k_reference.*.detect_oracle_separated_pairs)
export const RCR_KREF = [
  { k: "1", llama: 0.0, mistral: 0.0 },
  { k: "2", llama: 0.014, mistral: 0.016 },
  { k: "3", llama: 0.0905, mistral: 0.1025 },
  { k: "5", llama: 0.4785, mistral: 0.5695 },
  { k: "10", llama: 0.5765, mistral: 0.785 },
  { k: "25", llama: 0.8375, mistral: 0.881 },
  { k: "50", llama: 0.9305, mistral: 0.861 },
  { k: "all", llama: 1.0, mistral: 1.0 },
];
// research/ssr_pilot/results/rcrc/extended_analysis.json (by_family, E2 pairwise reversal)
export const RCR_FAMILY = [
  { label: "Banker's", value: 20.97 },
  { label: "Synchronization", value: 10.04 },
  { label: "Scheduling", value: 0 },
];

export interface RcrContribution {
  id: string;
  title: string;
  summary: string;
  finding: string;
}

export const RCR_CONTRIBUTIONS: RcrContribution[] = [
  {
    id: "1",
    title: "Exhaustive Reference-Choice Sensitivity & Instability",
    summary: "First systematic audit of benchmark identifiability under combinatorial reference sets (50,000 Monte Carlo draws across task solution spaces V(x)).",
    finding: "Holding outputs and tasks fixed, swapping only the chosen gold reference flips head-to-head winners 17.56% of the time and causes ranking instability (Kendall τb = 0.618 ± 0.351).",
  },
  {
    id: "2",
    title: "Quantification of Detection Loss & The Attenuation Law",
    summary: "Proving that single-reference evaluation compresses score variance and blinds benchmarks to statistically significant model superiority.",
    finding: "Single-reference evaluators miss true model separation in ≥99.99% of draws, retaining only 12–18% of the true performance gap due to the exact law: E[E2] = E3 / |V(x)|.",
  },
  {
    id: "3",
    title: "Reference-Invariant Execution Oracles & k-Reference Remedy",
    summary: "Replacing brittle reference matching with executable semantic simulation, or multi-reference sampling when an oracle cannot be built.",
    finding: "The semantic validator (E3) removes reference dependence by construction (τb = 1.000, 0% reversals). If unavailable, matching against k ≈ 25 references recovers ~85% of detection power.",
  },
];

export interface RcrModelScore {
  model: string;
  e1Exact: string;
  e2Norm: string;
  e3Oracle: string;
  frr: string;
}

export const RCR_MODEL_SCORES: RcrModelScore[] = [
  { model: "qwen3:8b", e1Exact: "4.86% (14/288)", e2Norm: "13.19% (38/288)", e3Oracle: "30.90% (89/288)", frr: "57.3%" },
  { model: "gemma2:9b", e1Exact: "0.69% (2/288)", e2Norm: "2.43% (7/288)", e3Oracle: "17.01% (49/288)", frr: "85.7%" },
  { model: "mistral:7b-instruct", e1Exact: "0.00% (0/288)", e2Norm: "3.47% (10/288)", e3Oracle: "7.64% (22/288)", frr: "77.3%" },
  { model: "llama3.1:8b", e1Exact: "0.00% (0/288)", e2Norm: "0.35% (1/288)", e3Oracle: "6.60% (19/288)", frr: "94.7%" },
];

export interface RcrPairwiseDetection {
  pair: string;
  oracleP: string;
  decision: string;
  e1P: string;
  e1MissRate: string;
  e2P: string;
  e2MissRate: string;
}

export const RCR_PAIRWISE_DETECTION: RcrPairwiseDetection[] = [
  { pair: "llama3.1:8b vs qwen3:8b", oracleP: "0.0126", decision: "qwen3 better (p < 0.05)", e1P: "0.991", e1MissRate: "100.00%", e2P: "0.929", e2MissRate: "99.99%" },
  { pair: "mistral:7b vs qwen3:8b", oracleP: "0.0175", decision: "qwen3 better (p < 0.05)", e1P: "0.991", e1MissRate: "100.00%", e2P: "0.928", e2MissRate: "99.99%" },
  { pair: "gemma2:9b vs qwen3:8b", oracleP: "0.1998", decision: "not separated (near-tie)", e1P: "0.992", e1MissRate: "—", e2P: "0.946", e2MissRate: "—" },
  { pair: "gemma2:9b vs llama3.1:8b", oracleP: "0.1998", decision: "not separated (near-tie)", e1P: "1.000", e1MissRate: "—", e2P: "0.991", e2MissRate: "—" },
  { pair: "gemma2:9b vs mistral:7b", oracleP: "0.1998", decision: "not separated (near-tie)", e1P: "1.000", e1MissRate: "—", e2P: "0.991", e2MissRate: "—" },
  { pair: "llama3.1:8b vs mistral:7b", oracleP: "0.7948", decision: "not separated (near-tie)", e1P: "1.000", e1MissRate: "—", e2P: "0.995", e2MissRate: "—" },
];

