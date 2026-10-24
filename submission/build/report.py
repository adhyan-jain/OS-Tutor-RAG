import sys, json, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import os
HERE=os.path.dirname(os.path.abspath(__file__)); SUB=os.path.abspath(os.path.join(HERE,".."))
F=SUB+"/figures/"
OUT=SUB+"/OS_Tutor_RAG_Report.docx"
pages=json.load(open(HERE+"/toc_pages.json")) if len(sys.argv)>1 else {}
TRANSCRIPT=json.load(open(HERE+"/transcript.json"))
TEAL=RGBColor(0x0f,0x76,0x6e); INKC=RGBColor(0x1e,0x21,0x28)

d=Document()
s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
s.left_margin=s.right_margin=Cm(2.5); s.top_margin=Cm(2.3); s.bottom_margin=Cm(2.3)
st=d.styles["Normal"]; st.font.name="Times New Roman"; st.font.size=Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman")
st.paragraph_format.line_spacing=1.3; st.paragraph_format.space_after=Pt(6)
for n,sz in (("Heading 1",16),("Heading 2",13),("Heading 3",12)):
    h=d.styles[n]; h.font.name="Times New Roman"; h.font.size=Pt(sz); h.font.bold=True; h.font.color.rgb=RGBColor(0x1e,0x21,0x28)
    h.element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman")
    h.paragraph_format.space_before=Pt(14 if n=="Heading 1" else 10); h.paragraph_format.space_after=Pt(6); h.paragraph_format.keep_with_next=True

def P(t="",bold=False,italic=False,align=None,size=None,color=None,after=None):
    p=d.add_paragraph(); r=p.add_run(t); r.bold=bold; r.italic=italic
    if size: r.font.size=Pt(size)
    if color: r.font.color.rgb=color
    if align=="c": p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    if align=="j": p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    if after is not None: p.paragraph_format.space_after=Pt(after)
    return p
def J(t): return P(t,align="j")
def B(t,lead=None):
    p=d.add_paragraph(style="List Bullet")
    if lead: r=p.add_run(lead); r.bold=True
    p.add_run(t); p.paragraph_format.space_after=Pt(3); return p
def H1(t): 
    h=d.add_heading(t,1); return h
def H2(t): return d.add_heading(t,2)
def CODE(t):
    for line in t.strip("\n").split("\n"):
        p=d.add_paragraph(); r=p.add_run(line if line else " "); r.font.name="Courier New"; r.font.size=Pt(9)
        r._element.rPr.rFonts.set(qn("w:eastAsia"),"Courier New")
        p.paragraph_format.left_indent=Cm(0.6); p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
        sh=OxmlElement("w:shd"); sh.set(qn("w:val"),"clear"); sh.set(qn("w:fill"),"F0EDE6"); p._p.get_or_add_pPr().append(sh)
    d.add_paragraph().paragraph_format.space_after=Pt(2)
def shade(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); sh=OxmlElement("w:shd"); sh.set(qn("w:val"),"clear"); sh.set(qn("w:fill"),fill); tcPr.append(sh)
def TABLE(rows,widths=None,caption=None,fs=10):
    if caption:
        c=P(caption,bold=True,size=10.5,after=3); c.paragraph_format.keep_with_next=True
    t=d.add_table(rows=len(rows),cols=len(rows[0])); t.style="Table Grid"; t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i,j); c.text=""; p=c.paragraphs[0]; r=p.add_run(str(v)); r.font.size=Pt(fs); r.bold=(i==0)
            p.paragraph_format.space_after=Pt(1); p.paragraph_format.line_spacing=1.1
            if i==0: shade(c,"E3EFEC")
            if widths: c.width=Cm(widths[j])
            if i<len(rows)-1: p.paragraph_format.keep_with_next=True
    if widths:
        for j,w in enumerate(widths): t.columns[j].width=Cm(w)
    d.add_paragraph().paragraph_format.space_after=Pt(2)
def FIG(path,w,cap):
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(path,width=Cm(w))
    c=P(cap,italic=True,align="c",size=10)
def PB(): d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---------------- title page
P("VIT",bold=True,align="c",size=34,color=TEAL,after=0)
P("Vellore Institute of Technology",bold=True,align="c",size=14,after=30)
P("PROJECT REPORT",bold=True,align="c",size=16,after=24)
for lab,val in (("CC:","BCSE307P"),("CN:","Operating Systems"),("Title:","OS-Tutor-RAG: A Retrieval-Augmented Socratic Tutor for Operating Systems, with a Measured Evaluation and a Study of Reference-Choice Robustness in Executable Benchmarks")):
    p=d.add_paragraph(); p.paragraph_format.left_indent=Cm(1.5); p.paragraph_format.space_after=Pt(10)
    r=p.add_run(lab+"  "); r.bold=True; r.font.size=Pt(14); r2=p.add_run(val); r2.font.size=Pt(14)
P("",after=30)
P("Submitted by",italic=True,align="c",after=4)
P("Adhyan Jain (24BCI0111)",bold=True,align="c",after=0)
P("Atharva Sheersh Pandey (24BCI0069)",bold=True,align="c",after=14)
P("Faculty: Dr. Jagalingam      Slot: B1+TB1      Semester: Fall 2026-27",align="c",size=11,after=4)
P("October 2026",align="c",size=11)
PB()

# ---------------- TOC (manual two-pass)
SECS=["Introduction","Literature Review","Problem Statement","Objectives","Methodology","Results and Discussion","Conclusion","Limitations","Future Work","References"]
P("Table of Contents",bold=True,size=16,after=10)
for i,sname in enumerate(SECS,1):
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(5)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16),alignment=2,leader=1)
    p.add_run(f"{i}.  {sname}\t{pages.get(sname,'')}")
sub=[("5.1  System overview","Methodology"),("5.2  Ingestion and chunking","Methodology"),("5.3  Retrieval and context expansion","Methodology"),("5.4  Generation: the prompts","Methodology"),("5.5  The tutoring layer","Methodology"),("5.6  Evaluation protocol","Methodology"),("5.7  Research protocol: RCR","Methodology"),
     ("6.1  Retrieval and defects","Results and Discussion"),("6.2  Prompt results","Results and Discussion"),("6.3  Noise floor","Results and Discussion"),("6.4  The tutoring layer","Results and Discussion"),("6.5  Research track: RCR results","Results and Discussion")]
P("",after=2)
P("Principal subsections",italic=True,size=10.5,after=2)
for t,_ in sub:
    p=d.add_paragraph(); p.paragraph_format.left_indent=Cm(1); p.paragraph_format.space_after=Pt(1)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16),alignment=2,leader=1)
    r=p.add_run(f"{t}\t{pages.get(t,'')}"); r.font.size=Pt(11)
PB()

# ---------------- 1 Intro
H1("1. Introduction")
J("Students in an introductory Operating Systems (OS) course meet a dense vocabulary almost at once: processes, system calls, context switches, paging, locks, semaphores, deadlock. Lecture decks are terse by design, and a textbook chapter assumes a reader who already knows what to look for. A student who is stuck at eleven at night has two usual options: a general-purpose chatbot, which answers fluently but is not tied to the course and sometimes invents details, or a search through slides that never explains anything.")
J("Retrieval-Augmented Generation (RAG) addresses the first problem by making a language model answer from retrieved passages instead of from memory alone. It does not, by itself, make the system a good tutor. A tutor does more than answer. It notices what the student already understands, asks a short question to check, gives a hint before the answer, corrects a specific wrong belief gently, stays patient with a student who says \"I don't get it\", and, for a student who does not know what to ask, suggests sensible next questions.")
J("This project, OS-Tutor-RAG (called \"OS Tutor\" in the interface), builds both halves. The first half is a RAG pipeline over the course's own lecture decks, OSTEP textbook chapters and lab handouts, built as a controlled comparison so that every design choice (chunking, retrieval technique, reranking, diversification, prompting) is backed by a measurement rather than by convention. The second half is a tutoring layer built on one central rule: pedagogical decisions live in tested code and the language model only phrases what the code has already decided.")
J("The project has a second, research half. While evaluating models on executable OS tasks (CPU scheduling, thread synchronisation, the Banker's algorithm) we found that when many different answers are all correct, the choice of which one to store as the gold reference changes how models are ranked and hides real differences between them. We call this Reference-Choice Robustness (RCR) and study it with exhaustive enumeration of every valid answer, 50,000 sampled reference sets, four local models and, in a preregistered follow-up, four Claude models (Sections 5.7 and 6.5). The two halves share one theme: before comparing systems, check whether the evaluation can actually resolve the difference you care about.")

# ---------------- 2 LR
H1("2. Literature Review")
J("Five works shape the engineering design (the research half is placed in Section 2.7). Each is summarised with the decision it informed here.")
H2("2.1 Retrieval-augmented generation")
J("Lewis et al. (2020) introduced RAG: a generator conditioned on passages retrieved from an external index, so that knowledge can be updated by editing the index and answers can point to sources. This is the architectural premise of OS Tutor. The paper also frames the retrieval and generation components as separately measurable, which motivated our split between retrieval-side and generation-side metrics.")
H2("2.2 Dense passage retrieval")
J("Karpukhin et al. (2020) showed that learned dense embeddings of questions and passages can outperform BM25 on open-domain question answering, because they match meaning rather than words. Our retrieval comparison tests this claim on a small, single-course corpus; we use the BGE-large embedding model (Xiao et al., 2023) and find dense retrieval reaches recall@5 of 1.000 while BM25 reaches 0.885 on the corrected benchmark.")
H2("2.3 Query transformation: HyDE")
J("Gao et al. (2022) proposed Hypothetical Document Embeddings: ask a model to write a plausible answer, embed that, and retrieve with it. The intuition is that an answer sits closer to answer-bearing passages than the question does. We implement HyDE and a multi-query variant and measure them; HyDE improves retrieval breadth (full@5 0.692 against 0.577 for dense) but the gain does not survive to answer quality.")
H2("2.4 Automated RAG evaluation: RAGAS")
J("Es et al. (2023) defined reference-free and reference-based metrics for RAG (faithfulness, answer relevancy, context precision and recall) computed with an LLM judge. We use RAGAS with a local judge. Our own findings add a caution that the paper's framework makes easy to miss: faithfulness rewards refusal, so a system that refuses everything scores 1.0.")
H2("2.5 LLM-as-a-judge")
J("Zheng et al. (2023) examined using strong LLMs to grade LLM outputs and catalogued their biases, including self-preference and verbosity. We took one direct design consequence: the judge (qwen2.5:7b) is from a different model family than the generator (llama3), to avoid grading a model's own style favourably. Our 7B judge is far weaker than the judges that paper studies, which we state as a limitation.")
H2("2.6 Tutoring and scaffolding")
J("The instructional design follows the long-standing notion of scaffolding (Wood, Bruner and Ross, 1976): support that is withdrawn as the learner gains competence. In the tutoring layer this appears as a ladder of hint, then a narrower scaffold question, then a concise explanation after repeated misses, and as a concept state that moves from UNKNOWN towards MASTERED.")

H2("2.7 Evaluation against references, and multi-valued truth")
J("The research half builds on work showing that reference choice affects reference-based metrics. Casola et al. (2025) show that summarization metrics and even system rankings vary with the human reference set, and Jeong et al. (2026) show the same for chest X-ray report evaluation. Evaluators that score against sets of valid solutions already exist (OTAP, Barazandeh et al., 2026), and HypoSpace (Chen et al., 2026) pairs exactly enumerated admissible sets with deterministic validators, but asks how much of the admissible set a model covers, not how much an evaluator loses by matching one reference. Our contribution is narrower than the general claim that references matter: a controlled protocol where the full valid set is enumerated and a reference-independent validator gives the true ranking, so reference choice can be varied as an experimental factor and the loss of detection power measured exactly. We do not claim to be first.")

# ---------------- 3 PS
H1("3. Problem Statement")
J("Existing options for a student learning OS fail in complementary ways. Slides and textbooks are authoritative but passive. General chatbots are interactive but ungrounded, so a student cannot tell a correct explanation from a plausible fabrication. A plain RAG chatbot is grounded but still behaves like a search box: it answers the question asked, says nothing about what to ask next, and gives a student who does not know the subject no way in.")
J("A third problem concerns evaluation itself: benchmarks for multi-step reasoning usually store one gold trajectory per task, yet in operating-systems tasks many trajectories are correct. It is unknown how much a benchmark's conclusions depend on that arbitrary choice. The problem addressed is therefore three-fold: the first two parts are engineering and the third is a measurement question. The first two are as follows. (1) Build a RAG pipeline over OS course material whose configuration is justified by measurement, including the measurement of the evaluation method itself. (2) Make the chatbot behave as a Socratic tutor that is friendly, interactive, checks understanding with graded questions, adapts when the student struggles, and proposes good follow-up questions even when the student knows nothing about the topic, while keeping every answer grounded in the course material.")

# ---------------- 4 Objectives
H1("4. Objectives")
for lead,t in (
 ("O1. ","Ingest and index the course material (PPTX decks, PDF chapters, DOCX handouts) without silently losing content such as tables or legacy-format files."),
 ("O2. ","Compare chunking, retrieval, reranking, diversification and prompting strategies against a hand-built golden question set, and adopt only what the evidence supports."),
 ("O3. ","Quantify the reliability of the evaluation itself (run-to-run noise, metric blind spots) so that conclusions are not drawn from differences below the noise."),
 ("O4. ","Provide a streaming web chatbot with three explanation levels (ELI5, undergraduate, exam preparation) and source citations."),
 ("O5. ","Implement a tutoring layer: 30 authored concepts with 96 graded questions, a concept-state machine, a hint, scaffold, explain-after-two-misses ladder, 16 misconception probes, a three-question quiz mode, difficulty detection and fixed, safe replies to distress, off-topic and prompt-injection messages."),
 ("O6. ","Offer an orientation reply, a learning path, starter chips and three layers of follow-up suggestions so that a student who knows nothing can still move forward."),
 ("O7. ","Research objective: measure how much model scores, rankings, winner decisions and statistical significance change when only the gold reference is replaced by another valid trajectory (RCR), test whether the effect persists for stronger models in a preregistered follow-up, and evaluate remedies (multi-reference scoring)."),
 ("O8. ","Keep the work reproducible and honest about limits: automated tests for the tutoring policy (877 tutor tests plus 427 pre-existing), recorded refutations, and stated caveats.")):
    B(t,lead)

# ---------------- 5 Method
H1("5. Methodology")
H2("5.1 System overview")
J("Figure 1 shows the system. An offline stage turns the course files into a searchable index. An online stage retrieves passages for each question, expands them to their parent slide or page, builds a teaching prompt and streams the model's answer to the browser over Server-Sent Events (SSE). The tutoring layer wraps every turn in two half-steps. plan_turn runs before retrieval and either answers entirely with authored text chosen by code (triage, orientation, a graded reply to the pending question, a hint, a quiz question), costing no retrieval and usually no model call, or hands the message to the RAG pipeline as a plan. finish_rag runs after the grounded answer and appends at most one Socratic question and the follow-up chips. The server streams three kinds of event over SSE: token (answer text), ui (chips, question card, concept state) and sources.")
FIG(F+"architecture.png",16,"Figure 1. Architecture of OS-Tutor-RAG: the tutoring layer (red) wraps the RAG pipeline (teal) on every turn.")
H2("5.2 Ingestion and chunking")
J("The corpus used for the measurements in this report was 22 extracted documents from 10 source files (5 PPTX decks, 4 OSTEP PDF chapters and one DOCX of 13 sections) covering processes and shell programming. The live system's corpus has since grown: all 36 indexed files in data/raw (adding memory management, concurrency, deadlock and IPC material) are searchable; the measurements were not repeated on it. Extractors read each slide's title, bullets and table cells, each PDF page, and each DOCX heading section.")
J("Chunking is matched to the format rather than treated as a tunable axis. PPTX uses structure-aware chunking: each bullet becomes a small child chunk prefixed with its slide title, and the whole slide is stored as its parent. PDF uses page-aware semantic chunking bounded by the page, with the page as the parent. DOCX uses overlapping windows with the section as parent. The child/parent design (\"small-to-big\") matches on narrow passages and generates from their full context.")
H2("5.3 Retrieval and context expansion")
J("Children are embedded with BAAI/bge-large-en-v1.5 and indexed with FAISS. The default retriever is dense search. Implemented alternatives are BM25, hybrid Reciprocal Rank Fusion (RRF), HyDE, and a multi-query wrapper that generates reformulations, retrieves for each and fuses by RRF. Optional rerankers (a cross-encoder, bge-reranker-large, and a pointwise LLM scorer) and Maximal Marginal Relevance (MMR) diversification are implemented and were measured, then turned off by default because they did not help. After selection, each child is replaced by its parent text capped at 400 tokens and windowed around the match when larger, so that matching stays precise while the model reads complete context.")
H2("5.4 Generation: the prompts")
J("Generation runs on a local Ollama server (llama3 by default) at temperature 0. Two prompts matter and they are different things. The evaluation prompt (\"few_shot\") is the one the RAGAS experiments scored. The teaching prompt is what students actually receive in the app, and it is NOT the few_shot prompt: it was written for explaining to a beginner and for leaving the questioning to the tutoring layer, and no RAGAS metric has been computed for it. Both are reproduced exactly.")
P("Evaluation prompt (\"few_shot\", the measured default):",bold=True,after=2)
CODE("""Answer the question using only the context below. If the context
doesn't contain the answer, say so.

Answer in continuous prose, stating each fact once. Do not add preamble
about the context.

Example question: What does the OS do when it creates a process?
Example answer: The OS allocates memory and creates the memory image,
loads the code and data from the executable on disk, creates the runtime
stack and heap, and opens basic files.

Example question: What are user mode and kernel mode?
Example answer: CPU hardware has multiple privilege levels: user mode
runs user code, and kernel mode runs OS code such as system calls.

Context:
{context}

Question: {query}

Answer:""")
P("Teaching prompt (undergraduate level; ELI5 and exam-prep differ in the persona paragraph):",bold=True,after=2)
CODE("""You are a knowledgeable teaching assistant for an undergraduate
operating systems course, working from the context below. Assume the
student knows basic CS fundamentals (variables, functions, memory, the
CPU) and use standard OS terminology, with an analogy only where it
clarifies a genuinely tricky point.

{instructions}      <- the guided block below, or the direct block
Ground everything in the context below. If the context does not cover
part of the question, say so plainly rather than filling the gap from
outside knowledge.

{history_block}{misconception_block}{continuation_block}
Context:
{context}

Student's message: {query}

Your turn:""")
P("Guided instructions (default; 'Guided questions' switched on), abridged:",bold=True,after=2)
CODE("""Tone: you are a patient, friendly tutor, like a helpful senior guiding a
junior. Be warm and encouraging without gushing; never condescending.
Assume the student may know nothing about the topic: define any term a
beginner would not know the first time you use it, and keep sentences short.

How to answer:
- Answer what the student actually asked, directly and completely, from the
  context. Explain first; never withhold the explanation to make the student
  guess. A separate step of the app adds one short check-your-understanding
  question after your answer, so do NOT end with a question of your own and
  do NOT quiz the student.
- Keep it focused: the idea, why it matters, and one concrete example or
  analogy when it helps.
- If a note below says the student may hold a misconception, address it
  gently inside your explanation without making them feel foolish.
- If the message is a short continuation ("continue", "go on"), continue
  naturally from exactly where the conversation left off.""")
J("With the Guided questions toggle off, a second block is used instead: answer completely and ask the student no questions. The misconception note that the prompt carries now comes from deterministic patterns matched against the student's question (16 authored misconceptions), which replaced a per-message model call that classified the question; this removes one blocking model call and its latency from every turn. The old call remains behind an environment flag as a fallback.")
J("Three other prompts exist and were measured: \"strict\" (answer or say the context lacks the answer), \"part_coverage\" (answer each part the context supports) and \"cot\" (a labelled Reasoning section before the Answer, stripped before scoring).")
H2("5.5 The tutoring layer")
J("The layer (src/tutor) follows one guiding rule: the model never decides whether an answer is right; policy lives in tested code and a model may only phrase an outcome. The state of one conversation (concept states, the pending question, the quiz, the chips already shown) is kept per chat. Its parts are:")
B(" authored course knowledge: 30 concepts in five units (Foundations, Processes, Memory, Concurrency, IPC and tools), each with detection aliases, prerequisites, a description and an importance; 96 graded questions; 16 misconceptions. The longest matching alias wins, so \"page fault\" maps to demand paging rather than to the generic \"process\". Each question's model answer is itself tested to pass its own answer key, and a hint must not be parroted back as an answer.","Knowledge model:")
B(" every message first passes a deterministic filter for distress (\"I'm going to fail\"), clearly off-topic requests and prompt-injection attempts (\"ignore your previous instructions\"). Each gets a fixed, kind reply that does not depend on a model being reachable; a distressed student is encouraged to talk to the instructor and offered one small next step, not quizzed.","Triage:")
B(" deterministic intent detection (hint, just tell me, example, skip, pause, quiz, path, lost, greeting, continue, prerequisites, what next) and difficulty detection (confused, frustrated, overwhelmed, asking to repeat, uncertain). A struggling student first gets a simpler explanation at ELI5 level, then, if it still has not clicked, the full explanation. A firm new question while a question is pending (\"Compare FCFS and SJF\") is never graded as an attempt.","Intent and difficulty:")
B(" each concept moves through UNKNOWN, INTRODUCED, ATTEMPTED, PARTIALLY_UNDERSTOOD, UNDERSTOOD and MASTERED. Every change goes through one function that records its source. There is no wall clock: a turn counter implements the cooldown, so behaviour is reproducible and testable. MASTERED is reachable only from UNDERSTOOD through a correct transfer question.","Concept state machine:")
B(" a correct or partial answer is judged by regex answer keys (CORRECT, PARTIAL, MISCONCEPTION, UNCLEAR). Feedback is honest about which: a partial answer is told what is right and gets the scaffold; a misconception gets a probing question first and the correction only after two misses; after two non-correct attempts the tutor stops asking and explains. A correct answer earns, in quiz mode, a harder question at the next level of the ladder (recall, understanding, application, analysis).","Grading and the hint ladder:")
B(" after the grounded answer, at most one short question about the concept just discussed (a new concept starts with recall, a partial one with interpretation, an understood one with transfer), never repeating a question and never re-testing an understood concept, and never stacking a second question on a pending one. A Guided questions switch in the UI turns this off for plain answers.","One Socratic question per answer:")
B(" \"test my understanding\" starts three questions on one concept, then a short summary of how the student did.","Quiz mode:")
B(" for a student who knows nothing: a greeting or \"I'm new\" returns a short learning path built from the foundations, \"I don't know what to ask\" returns an orientation with starter chips, and the empty chat shows a course map. Follow-up chips come from three layers: authored, concept-aware chips (explain with an example, test my understanding, what to know first, how it connects to the next idea); chips built from the slide titles of the sources the answer was grounded in, which work for any topic in the corpus; and follow-up questions written by the model, validated by code before being shown. Every chip is a complete message, so tapping it is the same as typing it.","Orientation and follow-up suggestions:")
B(" two optional, fail-soft model calls. One phrases a reply to a free-text answer the answer keys cannot read and proposes a classification, which is clamped: at most one level up, never to UNDERSTOOD, never down. The other writes follow-up questions. A question written by the model has no answer key, so it is never graded and moves no concept state.","Where a model may help:")
H2("5.6 Evaluation protocol")
J("The pipeline is scored with RAGAS on a golden set of 26 questions (5-6 per topic: OS basics, process abstraction, process API, process execution mechanism, shell programming). Each question is paired with a ground-truth answer and the slide or page it is answerable from (source_parent_ids), and is worded unlike the slide title so a retriever cannot win by matching the heading. For each question the pipeline retrieves contexts and generates an answer; RAGAS then sends the judge model the question, the retrieved contexts, the generated answer and the ground truth, and the judge returns claim-level decisions from which seven metrics are computed.")
TABLE([["Metric","Judges","How it is computed (inputs to the judge)"],
 ["context_precision","retrieval","Fraction of retrieved contexts judged useful for the question (question, contexts, ground truth)"],
 ["context_recall","retrieval","Fraction of ground-truth claims supported by the contexts"],
 ["context_entity_recall","retrieval","Overlap of entities extracted from ground truth and from contexts (found unreliable here)"],
 ["faithfulness","generation","Answer split into claims; fraction entailed by the contexts (hallucination guard)"],
 ["answer_relevancy","generation","Questions regenerated from the answer, embedded and compared with the real question"],
 ["answer_similarity","generation","Embedding cosine between answer and ground truth"],
 ["answer_correctness","whole pipeline","Weighted blend of answer_similarity and an F1 over answer vs ground-truth statements"]],
 widths=[3.6,2.6,9.8],caption="Table 1. The seven RAGAS metrics.",fs=9.5)
J("Generation and judging are run in two passes (all answers first, then all scoring) because the generator and judge cannot share the 8 GB GPU. Retrieval is also measured directly, without any model in the loop, with recall@k, MRR and full@k (all required source parents present) against source_parent_ids. Costs quoted in USD are hypothetical, priced from token counts at published API rates; no paid API was called.")

H2("5.7 Research protocol: Reference-Choice Robustness")
J("Benchmark. 24 executable OS tasks (\"worlds\"): 8 CPU-scheduling, 8 synchronisation, 8 Banker's-algorithm. For every task the complete set V(x) of valid answers is enumerated by search (2 to 192 valid answers per task), and each answer is rechecked by a separately written validator. Each task is rendered in 3 surface variants and each prompt is run 4 times, giving 288 generations per model.")
J("Evaluators. E1 is exact string match against one reference; E2 is normalised trajectory match against one reference; E3 is a semantic validator that replays the answer through the system rules and never sees a reference. E3 is therefore reference-invariant by construction, and the study measures the cost of not using it.")
J("Reference vectors and metrics. A benchmark reference vector picks one valid answer per task; 50,000 vectors are sampled from the Cartesian product of all V(x). For each vector the models are rescored and we compute Kendall tau-b against the canonical ranking, the probability that the pairwise winner reverses between two vectors, how often the oracle ordering is recovered, and, with the world as the statistical unit (N = 24), a paired sign-flip test with Holm correction for whether a difference is detected. An attenuation law, E[E2] = E3/|V(x)|, explains the loss, and a k-reference remedy (an output passes if it matches any of k sampled references) is evaluated.")
J("Models. Main study: qwen3:8b, gemma2:9b, mistral:7b-instruct, llama3.1:8b (local, Ollama), 1,152 generations. Follow-up: claude-haiku-4-5, claude-sonnet-4-5, claude-haiku-5-5, claude-sonnet-5-5 through the headless Claude CLI (no tools, thinking off, empty working directory), 1,152 generations, under an analysis plan with four hypotheses frozen before any generation. The CLI does not expose sampling parameters, so this arm is reported separately and not pooled with the local models.")

# ---------------- 6 Results
H1("6. Results and Discussion")
H2("6.1 Retrieval and defects")
J("The most important early result was negative for the project's original premise. A chunking defect, slide titles indexed as standalone chunks, made BM25 look dramatically worse than dense retrieval (answer_correctness 0.509 against 0.616), because twelve of 81 slides have question-shaped titles that match a user's question lexically while containing no answer. After the fix, and after parent expansion (generation had been receiving only the ~50-character child), refusals fell from 11.7% to about 0%. Fixing a defect was worth more than choosing among techniques.")
TABLE([["Technique","R@1","R@3","R@5","R@10","full@5","MRR"],
 ["dense","0.769","0.962","1.000","1.000","0.577","0.875"],
 ["hyde","0.654","0.923","1.000","1.000","0.692","0.804"],
 ["dense + multi_query","0.808","0.923","0.962","1.000","0.577","0.873"],
 ["hybrid_rrf + multi_query","0.769","0.885","0.962","0.962","0.654","0.848"],
 ["hybrid_rrf","0.769","0.808","0.923","1.000","0.538","0.826"],
 ["bm25","0.654","0.731","0.885","0.923","0.462","0.736"]],
 widths=[5,1.8,1.8,1.8,1.8,2,1.8],caption="Table 2. Retrieval metrics on the corrected golden set (26 questions).")
FIG(F+"retrieval.png",11.5,"Figure 2. Dense retrieval saturates recall@5; HyDE leads full@5; no technique dominates.")
J("Dense retrieval is the best all-rounder and the only technique needing no model call. HyDE buys breadth (full@5) at the cost of precision (R@1); multi-query buys precision but dilutes recall. A second benchmark effect is worth recording: the benchmark itself was biased against lexical retrieval. Rewriting questions to avoid the slide's wording raised BM25's recall@5 from 0.500 to 0.885 with no change to BM25, so the original claim that BM25 fails half the time measured the question set.")
P("Post-retrieval refinements all measured worse than leaving them out:",after=2).paragraph_format.keep_with_next=True
TABLE([["Stage","Measured effect"],
 ["Cross-encoder reranking","-0.05 answer_correctness on the biased benchmark; +0.013 after correction (within noise)"],
 ["MMR diversification","-0.038 hit@8 (drops a correct slide)"],
 ["Per-parent capping","no effect on hit rate"],
 ["BM25 fusion in hybrid_rrf","-0.077 recall@5 against dense alone"]],widths=[5.5,10.5],caption="Table 3. Refinement stages.")
P("Eight-variant sweep (26 questions, 5 query variants where multi-query is on):",after=2).paragraph_format.keep_with_next=True
TABLE([["Variant","composite","ans_corr","faithful.","ctx_recall","LLM calls"],
 ["dense + multi_query","0.772","0.662","0.958","0.936","480"],
 ["hyde + cross_encoder","0.764","0.644","0.958","0.978","491"],
 ["hyde","0.752","0.631","0.929","0.958","510"],
 ["dense + cross_encoder","0.744","0.642","0.949","0.926","448"],
 ["hyde + multi_query + cross_enc.","0.743","0.656","0.882","0.968","593"],
 ["dense","0.740","0.629","0.899","0.942","451"],
 ["hyde + multi_query","0.734","0.637","0.912","0.960","615"],
 ["dense + multi_query + cross_enc.","0.720","0.607","0.883","0.936","471"]],
 widths=[5.8,2,2,2,2.2,2],caption="Table 4. Focused sweep. The spread across all eight is 0.052; cost and quality were anti-correlated.")
H2("6.2 Prompt results")
J("Against the identical best configuration, two worked examples in the prompt raised answer_correctness more than the whole retrieval sweep. The diagnosis was that answers lost points to statement granularity (a content-identical answer scored 0.56 because it split one reference statement into two bullets), since answer_correctness compares sets of statements.")
TABLE([["Prompt","composite","ans_corr","faithfulness","ctx_recall"],
 ["strict (previous default)","0.763","0.664","0.942","0.946"],
 ["few_shot (adopted)","0.784","0.756","0.986","0.928"],
 ["part_coverage","0.712","0.631","0.819","0.936"]],widths=[5.5,2.5,2.5,2.8,2.5],caption="Table 5. Prompt comparison on dense + multi_query.")
J("Chain-of-thought was the next hypothesis and was refuted: answer_correctness fell from 0.7478 to 0.6887 and faithfulness from 0.981 to 0.933, because the reasoning step shortened answers by 27% (26.0 against 35.6 words), and the lost words were lost statements. The part_coverage prompt invited the model to fill gaps from its own knowledge and dropped faithfulness to 0.819. Both are kept in the code as recorded negatives.")
FIG(F+"prompts.png",9.5,"Figure 3. Prompt choice (cot was scored in a separate run, separate run: few_shot 0.748, cot 0.689).")
H2("6.3 Noise floor and what can be believed")
J("The same configuration (dense + multi_query + cross-encoder, few_shot prompt) was scored twice and gave 0.7752 and 0.7478. The run-to-run noise floor on answer_correctness is therefore about 0.027, from stochastic multi-query variant generation and from nondeterministic numerics in the inference server that persist even at temperature 0. Figure 4 reads every result against it.")
FIG(F+"ablation.png",13.5,"Figure 4. Effect of each change on answer_correctness against the noise floor.")
J("Only the defect fixes, the few-shot prompt and the chain-of-thought regression are established. The reranking gain (+0.029) and the multi-query gain (+0.014) are not: the retrieval-technique comparison that occupies most of the effort lives inside its own error bars. Two further cautions came from the metrics. Faithfulness rewards refusal (a pipeline that refuses everything scores 1.0), so refusal rate was tracked beside it; and context_entity_recall was shown to be extraction disagreement rather than missing information (seven ground-truth entities, all present in the context, matched zero).")
H2("6.4 The tutoring layer")
J("The tutoring layer's decisions are deterministic, so it is evaluated by tests and live runs rather than by a judge model. The tutor suite (tests/tutor) has 877 passing tests, alongside 427 pre-existing tests that still pass. They check, among other things: that every question's model answer passes its own key and is classified CORRECT; that partial, misconception and unclear inputs are graded as such; that understanding is never regressed by a partial or unclear answer; that the advisory suggestion is clamped; that a question is not repeated and an understood concept is not re-tested; that a hint repeated back as an answer is not accepted; that distress, off-topic and injection messages get the fixed reply while no genuine course question trips triage; that every chip is a self-contained message that routes correctly and that chips are not repeated; that a firm new question mid-quiz is answered rather than graded; and an event-contract test of the API with retrieval and the model stubbed. A scripted dialogue (test_new_student_dialogue) follows a student who says \"I'm new to operating systems\" through the path, a tapped suggestion, the grounded answer and exactly one appended question. The system was also run end to end through the web interface with llama3.1:8b and mistral: starter, learning path, explanation, Socratic question, graded reply, hint chips and the progress pill.")
J("Figure 5 is real output of the engine (plan_turn and finish_rag) for a new student. The grounded answers are written by the model at run time, so a placeholder stands in for them; every tutor line below, including the path, the question, the scaffold, the grading feedback, the chips and the quiz opener, is produced by the code. Long lines are abridged with [...]; the driver is submission/build/transcript.py.")
def _abridge(t,n=230):
    t=" ".join(t.split()) if len(t)<=n else (" ".join(t[:n].split()[:-1])+" [...]")
    return t
for who,x in TRANSCRIPT:
    if who=="chips":
        p=d.add_paragraph(); p.paragraph_format.left_indent=Cm(1.2); p.paragraph_format.space_after=Pt(4)
        r=p.add_run("chips: "+"  |  ".join(x)); r.italic=True; r.font.size=Pt(9.5); r.font.color.rgb=TEAL
        continue
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(1); p.paragraph_format.keep_with_next=(who=="Student")
    p.paragraph_format.left_indent=Cm(0 if who=="Student" else 0.6)
    r=p.add_run(who+": "); r.bold=True; r.font.size=Pt(10); r.font.color.rgb=(INKC if who=="Student" else TEAL)
    paras=[q for q in x.split("\n\n") if q.strip()]
    first=True
    for q in paras[:3]:
        if not first:
            p=d.add_paragraph(); p.paragraph_format.left_indent=Cm(0.6); p.paragraph_format.space_after=Pt(1)
        r=p.add_run(_abridge(q.replace("**",""))); r.font.size=Pt(10); first=False
    if len(paras)>3:
        r=p.add_run(" [...]"); r.font.size=Pt(10)
P("Figure 5. Transcript of a new student with the real tutoring engine (abridged).",italic=True,align="c",size=10)
J("Two things the transcript shows. First, when the student says \"no idea\", the tutor does not mark an answer wrong: it normalises the uncertainty, restates the concept simply and offers an easier way in. Second, the tutor accepts a correct answer written in the student's own words, not only the textbook sentence, and then offers next steps that include a test of understanding.")
J("This is verification of intended behaviour, not evidence of learning gains. No study with students was run, and there is no RAGAS-style metric for pedagogy: the RAGAS results in 6.1-6.3 measure answer quality for the few_shot prompt, not the teaching prompt or the tutor's questions. The regex answer keys can miss a correct paraphrase; the clamped advisory call mitigates this but does not remove it.")
H2("6.5 Research track: Reference-Choice Robustness results")
J("Main study (four local models, 1,152 generations). Changing only the gold reference, with tasks, outputs and evaluator fixed, gave Kendall tau-b = 0.618 +/- 0.351 for E2 and reversed the pairwise winner in 17.56% of reference pairs (exact value 17.15%). E2 recovered the oracle ordering in only 13.63% of draws and E1 in 2.86%. The sharper finding is detection loss: the validator E3 finds qwen3:8b significantly better than llama3.1:8b and mistral:7b (Holm p = 0.013 and 0.018) under every reference choice, whereas E2 detects these differences in 5 of 50,000 draws (99.99% missed) and keeps only 12-18% of the true gap, exactly as the attenuation law predicts. 85.6% of the reversal mass sits in pairs the validator itself cannot separate, so the headline reversal rate is largely a near-tie effect. All local models were at the capability floor (validator scores 6.6-30.9%).")
J("Follow-up above the floor (four Claude models). To test whether the findings were a weak-model artefact, the identical benchmark was run on four Claude models. Four hypotheses were frozen in writing before generation (an internal, hash-stamped plan, not an external registration). Results are in Table R1 and the outcomes in Table R2.")
TABLE([["Model","Valid (E3)","E2 canonical","Canonical share of valid","CIF (95% CI)"],
 ["claude-sonnet-5-5","99.3%","55.6%","55.9%","3.30 (2.27-5.10)"],
 ["claude-haiku-5-5","98.3%","45.1%","45.9%","2.67 (2.01-3.73)"],
 ["claude-sonnet-4-5","79.9%","25.7%","32.2%","2.26 (1.36-3.58)"],
 ["claude-haiku-4-5","73.3%","32.3%","44.1%","3.11 (1.94-5.18)"]],
 widths=[4.0,2.4,2.8,3.4,3.4],caption="Table R1. Claude-family arm (24 tasks, 288 generations per model). CIF is the canonical inflation factor: valid outputs matching the canonical reference divided by the number expected if the model chose uniformly among valid answers.",fs=9.5)
TABLE([["Hypothesis","Prediction","Outcome"],
 ["H1 floor","At least 3 of 4 models reach 30% validity","Supported: 4 of 4 (73-99%)"],
 ["H2 detection loss","E2 detects validator-separated pairs in under 50% of draws","Supported: 3.0% pooled (1.7-4.3% per pair)"],
 ["H3 canonical inflation","CIF above 1 for every model, and models differ","Supported as written: CIF 2.26-3.30; the 'models differ' test is weak by construction, so only CIF above 1 is claimed"],
 ["H4 ranking distortion","Canonical E2 score ratio differs from E3 ratio by more than 1.5x","Not supported: largest factor 1.43"]],
 widths=[3.4,5.6,7.0],caption="Table R2. Preregistered hypotheses and outcomes for the Claude-family arm.",fs=9.5)
J("Under a uniformly random reference, E2 reversed the pairwise winner in 26.9% of reference pairs for these stronger models (tau-b = 0.472, oracle-ordering recovery 22.6%), higher than in the floor-limited main study. The attenuation law again held exactly (r = 1.000 over 92 model-task cells). Scoring against k = 5 references detected the validator-separated pairs in 36-44% of draws and k = 25 in 51-69%, compared with 2-5% for a single reference, so the multi-reference remedy helps but restores less power than in the main study.")
J("What can and cannot be claimed. The detection loss and the canonical bias (models produce the canonical solution two to three times more often than uniform choice among valid solutions) persist above the capability floor; the preregistered 1.5-fold ranking-distortion prediction failed and is reported as a failure. The study is an empirical measurement paper on one 24-task benchmark in one domain; it is not claimed to generalise. We have not audited how common single-reference matching is in planning benchmarks, where executable validators are standard, so the practical reach of the finding is unverified. Full manuscript: paper/PAPER_FINAL.md (Section 4.8 for the follow-up).")

# ---------------- 7 Conclusion
H1("7. Conclusion")
J("OS-Tutor-RAG delivers a grounded, streaming OS tutor and a tutoring layer that makes it behave like one. On the engineering side the central lesson is that measurement overturned the plan: the gains came from repairing silent defects (titles indexed as chunks, parents never read, tables and a legacy file never indexed) and from the answer prompt, not from choosing a cleverer retrieval technique, and the technique differences sit inside a measured noise floor of 0.027. On the tutoring side, the system explains first and then asks one graded Socratic question; escalates from hint to scaffold to explanation; probes 16 common misconceptions; runs a three-question quiz; answers a struggling student with a simpler explanation; and offers an orientation, a learning path, starter chips and three layers of follow-up suggestions so that a student who knows nothing can still ask a good next question. All decisions are made by tested code (877 tutor tests) and the model is used for phrasing. What is not yet shown is a learning gain: that needs a study with students.")
J("On the research side, an empirical study of Reference-Choice Robustness shows that, in OS tasks with many valid answers, scoring against one stored reference hides real model differences (reference matching detected validator-significant differences in 0.01% of draws for local models and 3.0% for Claude models) and, for weak models, makes weakly supported rankings arbitrary (17.56% winner reversals); models also over-produce the canonical solution by a factor of 2.3-3.3. The remedy is an executable validator, or failing that scoring against many references. The preregistered 1.5-fold ranking-distortion prediction was not met. The work is a scoped empirical case study, not a general proof.")
P("Source code and evidence: ",bold=True,after=0).paragraph_format.keep_with_next=True
P("https://github.com/adhyan-jain/OS-Tutor-RAG",color=TEAL)

# ---------------- 8 Limits
H1("8. Limitations")
for t in (
 "Small benchmark: 26 questions over a 22-document, 10-file corpus. Differences of a few hundredths are not resolvable.",
 "Weak judge: qwen2.5:7b is a local 7B model and was not validated against human grading; a human rubric was deliberately deferred.",
 "Single run per configuration, no significance testing; the one variance estimate (0.027) is large relative to the retrieval effects.",
 "The corpus has since grown to all 36 indexed files; none of the numbers in Section 6.1-6.3 were re-measured on it. The tutor-facing teaching prompt differs from the few_shot prompt that RAGAS scored, and was not scored.",
 "Metric weaknesses: context_entity_recall is unreliable on conceptual text and half of the completeness composite; faithfulness rewards refusal.",
 "Ground truth is less complete than the corpus, so a more complete correct answer can be penalised as extra statements.",
 "The tutoring layer is verified by unit and dialogue tests and live smoke runs only: no study with students and no RAGAS-style metric for pedagogy. Its 30 authored concepts cover the main course topics, not every question a student could ask; regex answer keys can miss paraphrases (the clamped advisory call mitigates this, not removes it).",
 "Local 7-9B models only (8 GB GPU): latency and answer quality are bounded by them; costs in USD are hypothetical.",
 "RCR: all behavioural results come from one 24-task OS benchmark; the local models were at a capability floor, the newest Claude models are near ceiling so the validator cannot separate them; the Claude arm used the CLI with provider-default sampling and may drift between model versions; the analysis plans are internal freezes, not external preregistrations, and the RCR metrics were defined after seeing pilot data; the validator is a simulator, not a human gold standard; and how common single-reference matching is in real benchmarks was not audited."):
    B(t)

# ---------------- 9 Future
H1("9. Future Work")
for lead,t in (
 ("Re-measure on the full corpus. ","Rebuild the golden set across all 36 indexed files with several correct source parents per question, and re-run the sweep with 3-5 repeats per configuration and paired significance tests."),
 ("Validate the judge. ","Hand-label a sample and measure agreement with qwen2.5:7b, and test a stronger judge."),
 ("Query decomposition. ","Test splitting two-part questions, since 17 of 26 questions ask two things."),
 ("Learning-gain study. ","Run a small pre/post study with students comparing the plain RAG chatbot with the tutoring layer, and define a measurable pedagogy metric (for example concept-state gain per session)."),
 ("Paraphrase-robust grading. ","Measure how often the regex keys miss a correct paraphrase on student data, and test whether wider keys or the advisory call close the gap."),
 ("Wider concept coverage. ","Author more concepts and questions beyond the current 30 and 96, and generate candidates with a model but review them by hand before they enter the policy."),
 ("Persistent learner profiles. ","Concept state is held in memory per chat; store it across sessions so the learning path adapts over a semester."),
 ("RCR. ","Replicate on a second domain with at least 65 tasks and competent models, upload the analysis plan to an external registry, audit how many published benchmarks score against a single reference, and release the validator as a benchmark-design tool.")):
    B(t,lead)

# ---------------- 10 refs
H1("10. References")
refs=[
 "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems 33. arXiv:2005.11401.",
 "Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., Yih, W. (2020). Dense passage retrieval for open-domain question answering. Proceedings of EMNLP 2020. arXiv:2004.04906.",
 "Gao, L., Ma, X., Lin, J., Callan, J. (2022). Precise zero-shot dense retrieval without relevance labels (HyDE). arXiv:2212.10496; ACL 2023.",
 "Es, S., James, J., Espinosa-Anke, L., Schockaert, S. (2023). RAGAS: Automated evaluation of retrieval augmented generation. arXiv:2309.15217; EACL 2024 (demonstrations).",
 "Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. NeurIPS 2023 Datasets and Benchmarks. arXiv:2306.05685.",
 "Xiao, S., Liu, Z., Zhang, P., Muennighoff, N. (2023). C-Pack: Packed Resources For General Chinese Embeddings (BGE models). arXiv:2309.07597.",
 "Wood, D., Bruner, J. S., Ross, G. (1976). The role of tutoring in problem solving. Journal of Child Psychology and Psychiatry 17(2), 89-100.",
 "Arpaci-Dusseau, R. H., Arpaci-Dusseau, A. C. Operating Systems: Three Easy Pieces (OSTEP). Arpaci-Dusseau Books (course reading).",
 "Casola, S., Liu, Y. J., Peng, S., Kraus, O., Gatt, A., Plank, B. (2025). References Matter: Investigating the Impact of Reference Set Variation on Summarization Evaluation. INLG 2025, 274-291. arXiv:2506.14335.",
 "Jeong, D. P., Li, C. Q., Hosseiny, H., Bhalla, N. M., Uyar Morency, F., Ravikumar, P., Lipton, Z. C., Oberst, M. (2026). Reporting Practice Matters: The Impact of Reference Choice on Chest X-ray Report Evaluation. arXiv:2609.19093.",
 "Barazandeh, B., Majumdar, S., Michailidis, G. (2026). OTAP: Structure-Aware Optimal Transport for Evaluating Planning and Execution in Agent Trajectories. arXiv:2607.17082.",
 "Chen, T., Lin, Yuan, Zou, He, Goyal, Ong, Liu (2026). HypoSpace: A Diagnostic Benchmark for Set-Valued Hypothesis Generation under Underdetermination and Sublinear Coverage Bounds. arXiv:2510.15614 (ICML 2026).",
 "Project repository: OS-Tutor-RAG, FINDINGS.md (defects F1-F16, analyses A1-A20) and paper/PAPER_FINAL.md (RCR). https://github.com/adhyan-jain/OS-Tutor-RAG"]
for i,r in enumerate(refs,1):
    p=P(f"[{i}]  {r}",align="j",after=4); p.paragraph_format.left_indent=Cm(1); p.paragraph_format.first_line_indent=Cm(-1)
P("arXiv identifiers [1]-[6] were checked against arxiv.org on 2026-10-24; [7] (Wood, Bruner & Ross 1976) and [8] (OSTEP) are standard textbook/journal citations.",italic=True,size=10)

# footer page numbers
sec=d.sections[0]; fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=fp.add_run()
for typ,txt in (("begin",None),(None," PAGE "),("end",None)):
    if typ: e=OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"),typ)
    else: e=OxmlElement("w:instrText"); e.set(qn("xml:space"),"preserve"); e.text=txt
    r._r.append(e)
d.save(OUT); print("saved")
