# Contradiction Map

Sources: the six area reports (2026-09-30). Analyses of causes are **hypotheses** unless the papers test them; where a claim rests on an abstract or snippet it is marked. A contradiction is never resolved by picking a winner; each row asks whether it is context-dependent behavior (CD), a missing control variable (MC), an evaluation artifact (EA) or an untested interaction (UI).

## C1. Does self-verification / self-correction help?
- **Helps:** Self-Verification (2212.09561, abstract only); Chain-of-Verification (2309.11495, abstract only): "reduces hallucination".
- **Hurts / no consensus:** Huang et al. (2310.01798): LLMs "struggle to self-correct... without external feedback"; Kamoi survey (2406.01297): "no consensus"; CRITIC (2305.11738): intrinsic self-correction gave "modest improvements or even deteriorated performance".
- **Analysis:** CRITIC's own data show gains when *external tools* supply feedback. CoVe answers verification questions independently, unlike Huang's intrinsic setting. Tasks, model generations and oracle leakage differ. Classification: MC (feedback independence, evidence source) plus UI (model strength x task). No retrieved paper crosses independence x evidence source x model strength.
- **Why it matters here:** an *execution-based* check is the one variant not contested. It is the reason executable verification is worth testing, not a proof it works for explanations.

## C2. Is LLM-judge self-preference real?
- **Real:** Wataoka et al. (2410.21819): GPT-4 significant self-preference; Yang et al. (2604.22891): substantial in several models; Panickssery et al. (2404.13076): correlates with self-recognition, causality "not fully validated".
- **Overstated / absent:** Roytburg et al. (2601.22548): only 51% of prior examples retain significance against an evaluator-quality baseline; Guey et al. (2606.20093): gap -5.1 pp, CI [-12.9, +2.7]; effects under ~13 pp not excluded.
- **Analysis:** EA plus MC. Judge quality is confounded with authorship; gold labels differ (perplexity vs LLM-derived oracle); Wataoka's perplexity/familiarity explanation and Yang's family-effect confound are unseparated. No paper uses human gold labels to disentangle them (Roytburg names this as future work).
- **Relevance:** the project's own pipeline uses a different-family judge (qwen2.5:7b judging llama3) to avoid this; the literature says the benefit of doing so is itself unresolved.

## C3. Do LLM judges agree with humans?
- **High:** MT-Bench (2306.05685): GPT-4 >80% agreement, equal to human-human.
- **Low or conditional:** order swap flips rankings (2305.17926, snippet); unsuitable for factual tasks (2305.01937); length bias (2404.04475); ~65% preference matching in some scientific-reasoning settings (cited second-hand in 2601.05473); MRBench human kappa 0.65-0.71 for tutor dimensions.
- **Analysis:** CD. High on open-ended chat preference with a strong judge; degrades on factual/expert/pedagogical tasks and under order/length confounds. **No study of judge validity on tutoring or OS answers was found.**

## C4. Do verifier false positives cause reward hacking?
- **Yes:** Helff et al. (2604.15149): models learn shortcuts accepted by extensional verifiers; Zhao et al. (2507.08794, abstract only): master-key tokens fool judges.
- **Bounded:** Zhang et al. (2607.11022, abstract only): held-out effect of leaky tests non-inferior (0.20 pt gap), though 47.57% of rewarded false positives are genuinely wrong code.
- **Analysis:** CD plus UI. 1-1.5B models, 400 steps, MBPP vs an inductive-reasoning task where enumeration is a cheap shortcut. Scale, training length and shortcut cost are not varied together.

## C5. Are citation / faithfulness metrics reliable?
- **Reliable (snippet only):** ALCE reports kappa 0.698 (recall) / 0.525 (precision) vs humans (2305.14627, unverified).
- **Unreliable:** Ramprasad and Wallace (2411.16638): metrics drop on hard cases, can be gamed by appended innocuous sentences; Qian et al. (2410.11217): over-penalize excess citations; FaithBench: detectors near 50% accuracy.
- **Analysis:** EA. Aggregate agreement on a benchmark dominated by easy cases is compatible with hard-case failure; pooled kappa hides stratified failure. Not verified in the ALCE paper itself.

## C6. Expansion, chunking and context: help or harm?
- **Query/document expansion:** helps weak retrievers, harms strong ones (2309.08541). HyDE and RAG-Fusion were proposed as generally useful (claims not read).
- **Semantic chunking:** "not justified by consistent performance gains" (2410.13070) vs sentence chunking matches semantic up to ~5k tokens with a "context cliff" beyond ~2.5k tokens (2601.14123); the first uses stitched synthetic documents and LLM-generated answers, the second excludes rerankers.
- **Context volume:** distractors hurt but random documents *raise* accuracy (The Power of Noise, SIGIR 2024, doi 10.1145/3626772.3657834); quality rises then falls with more passages (2410.05983); long-context beats RAG when resourced (2407.16833, abstract only).
- **Analysis:** MC (retriever strength, context length, hard-negative strength) and EA (synthetic benchmark construction). The project's own finding that reranking helps single-query retrieval but hurts multi-query (FINDINGS A16) is an instance of the same interaction; the literature has no factorial study of chunker x expansion x reranker x generator at fixed budget.

## C7. GraphRAG vs vanilla RAG
- **Underperforms:** GraphRAG-Bench (2506.05690): "frequently underperforms vanilla RAG"; page-level retrieval on a math textbook favors embeddings on cost-adjusted terms (2509.16780).
- **Complementary / wins:** RAG vs GraphRAG evaluation (2502.11371): complementary strengths; classroom study (2509.07846): GraphRAG Global wins comprehensiveness, vector wins directness, at 10-20x cost.
- **Analysis:** CD (single-hop vs multi-hop/summarization) plus EA (heterogeneous protocols; LLM-judged comprehensiveness vs accuracy). GraphRAG's ~47K-token context is a confound in one comparison.

## C8. Do LLM tutors improve or harm learning?
- **Improve:** Kestin (0.63-1.3 SD, one physics session); Rori (0.36-0.37 SD); Tutor CoPilot (+4 pp mastery).
- **Harm / no gain:** Bastani (abstract only): unguarded GPT lowered later scores by 17%; Nie (abstract only): engagement and exam participation fell; dissociation RCT (abstract only): higher scores, no higher knowledge gain; Prather: struggling novices compounded difficulties; Khanmigo (abstract only): 0.06-0.08 SD, low engagement.
- **Analysis:** MC plus CD. Guardrails/structure differ (Bastani contrast), population (novices vs others), outcome timing (immediate vs after withdrawal vs end-of-year), study length (one session to two years), comparison arm (none vs active learning). TutorLLM (the one RAG-tutor with real students, n = 30) found no significant effect.

## C9. Do simulated students agree with real ones?
- **Agree (abstract only):** Liu et al. (BJET 2025): item parameters from LLM respondents correlate >0.8 with human-calibrated ones.
- **Disagree:** Benedetto et al. (2024): r = 0.13 (p = 0.06) for simulated item difficulty; Yuan et al. (2026): "competence paradox".
- **Not tested:** PedagogicalRL (2025) trains and evaluates against a simulated student and states it is not validated with real students.
- **Analysis:** different constructs (item calibration with ensembles vs single-model weak-student roleplay vs dialogue behavior). Difficulty ranking is not reproduction of misconceptions.

## C10. Do tutor-quality benchmarks predict learning?
- MathTutorBench: solving ability "does not immediately translate to good teaching". MRBench: turn-level annotation says nothing about learning. LearnLM: expert preference. RCTs (Kestin, Rori, Bastani) measure learning directly. **No paper links a benchmark score to measured learning gain.**

## C11. Does chain-of-thought help code-execution reasoning?
- REval: CoT effective; CRUXEval: CoT does not help input prediction as much (grep-level); CodeCrash: CoT reduces but does not remove a 13.8% drop; CES: 81.42% coherent traces but only 46.92% correct, "suspiciously correct" outputs via NL shortcuts.
- **Analysis:** EA. Final-answer accuracy and trace coherence disagree; models, prompts, temperature and benchmarks differ.

## C12. Contamination: large or small effect?
- Large: leakage inflates ranks (2311.01964, snippet); GSM1k drop up to 8% (r^2 = 0.36 with generation probability).
- Small: the same GSM1k paper finds minimal overfitting in frontier models; 11 mitigation strategies fail to consistently restore clean performance (2503.16402).
- **Analysis:** CD by model family and size; measured size depends on how contamination is induced.

## C13. Do LLM self-explanations tell us about the model?
- Agarwal (2402.04614, abstract) and Dehghani (2502.18156): plausibility over faithfulness, invalid self-counterfactuals. Mayne (2602.02639): self-explanations raise behavior prediction 11-37% NSG.
- **Analysis:** different constructs (simulatability vs validity). Neither tests whether an explanation is correct about the world.

## Cross-cutting pattern
Most contradictions dissolve into *missing control variables* or *evaluation artifacts*, not into one side being wrong. The recurring pattern is that a metric or benchmark measures a proxy (agreement, similarity, perception) whose relation to the target (correctness, learning) is asserted and rarely tested.
