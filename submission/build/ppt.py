from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os,json
HERE=os.path.dirname(os.path.abspath(__file__)); SUB=os.path.abspath(os.path.join(HERE,".."))
F=SUB+"/figures/"
TR=json.load(open(HERE+"/transcript.json"))
TEAL=RGBColor(0x0f,0x76,0x6e); INK=RGBColor(0x1e,0x21,0x28); SOFT=RGBColor(0xe3,0xef,0xec); GREY=RGBColor(0x6b,0x6f,0x78); RED=RGBColor(0xb3,0x44,0x1f); PAPER=RGBColor(0xfa,0xf8,0xf4); WHITE=RGBColor(255,255,255)
prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
blank=prs.slide_layouts[6]
def tb(sl,x,y,w,h,text="",size=16,bold=False,color=INK,font="Calibri",align=None,anchor=None):
    s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=s.text_frame; tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(0.05); tf.margin_top=tf.margin_bottom=Inches(0.03)
    if anchor: tf.vertical_anchor=anchor
    p=tf.paragraphs[0]; r=p.add_run(); r.text=text; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name=font
    if align: p.alignment=align
    return s
def bullets(sl,x,y,w,h,items,size=16,gap=6,color=INK):
    s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=s.text_frame; tf.word_wrap=True
    for i,it in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.space_after=Pt(gap)
        lead,rest=(it if isinstance(it,tuple) else (None,it))
        r0=p.add_run(); r0.text="• "; r0.font.size=Pt(size); r0.font.color.rgb=TEAL; r0.font.bold=True; r0.font.name="Calibri"
        if lead:
            r=p.add_run(); r.text=lead+" "; r.font.bold=True; r.font.size=Pt(size); r.font.color.rgb=color; r.font.name="Calibri"
        r=p.add_run(); r.text=rest; r.font.size=Pt(size); r.font.color.rgb=color; r.font.name="Calibri"
    return s
def rect(sl,x,y,w,h,fill,line=None,shape=MSO_SHAPE.RECTANGLE):
    s=sl.shapes.add_shape(shape,Inches(x),Inches(y),Inches(w),Inches(h)); s.fill.solid(); s.fill.fore_color.rgb=fill
    if line: s.line.color.rgb=line; s.line.width=Pt(1)
    else: s.line.fill.background()
    s.shadow.inherit=False; return s
def header(sl,title,sub=None,n=None):
    rect(sl,0,0,13.333,0.12,TEAL)
    tb(sl,0.6,0.35,12,0.7,title,size=30,bold=True)
    if sub: tb(sl,0.6,1.0,12,0.4,sub,size=15,color=GREY)
    tb(sl,0.6,7.05,8,0.3,"OS-Tutor-RAG · VIT",size=10,color=GREY)
    if n: tb(sl,12.2,7.05,0.6,0.3,str(n),size=10,color=GREY,align=PP_ALIGN.RIGHT)
def notes(sl,t): sl.notes_slide.notes_text_frame.text=t
def card(sl,x,y,w,h,title,body,size=13,accent=TEAL):
    rect(sl,x,y,w,h,SOFT if accent==TEAL else RGBColor(0xfb,0xe9,0xe2))
    rect(sl,x,y,0.07,h,accent)
    tb(sl,x+0.2,y+0.08,w-0.3,0.4,title,size=15,bold=True,color=accent)
    tb(sl,x+0.2,y+0.5,w-0.3,h-0.55,body,size=size)

# 1 title
s=prs.slides.add_slide(blank); rect(s,0,0,13.333,7.5,TEAL)
tb(s,0.8,0.5,4,0.9,"VIT",size=44,bold=True,color=WHITE)
tb(s,0.8,1.25,8,0.4,"Vellore Institute of Technology",size=14,color=RGBColor(0xd5,0xeb,0xe7))
tb(s,0.8,2.2,11.5,1.8,"OS-Tutor-RAG",size=54,bold=True,color=WHITE)
tb(s,0.8,3.2,11.5,1.2,"A retrieval-augmented Socratic OS tutor, and a study of how the choice of gold reference changes benchmark conclusions",size=24,color=WHITE)
tb(s,0.8,5.0,7,0.4,"CC: BCSE307P     CN: Operating Systems",size=18,color=WHITE)
tb(s,0.8,5.5,9,0.4,"Adhyan Jain (24BCI0111)  ·  Atharva Sheersh Pandey (24BCI0069)",size=18,bold=True,color=WHITE)
tb(s,0.8,6.0,9,0.4,"Faculty: Dr. Jagalingam   ·   October 2026",size=14,color=RGBColor(0xd5,0xeb,0xe7))
notes(s,"Introduce the project in one sentence: a chatbot that answers from our own OS course material and teaches like a tutor rather than a search box. Mention both authors. Two parts: the OS tutor chatbot, and the research study (Reference-Choice Robustness). Placeholders in square brackets (course name, logo) must be filled before submission.")

# 2 intro & objective
s=prs.slides.add_slide(blank); header(s,"Introduction & Objective","Why a grounded chatbot is not yet a tutor",2)
tb(s,0.6,1.6,6,0.4,"The problem",size=20,bold=True,color=TEAL)
bullets(s,0.6,2.1,5.9,3.4,[("Slides are passive.","Terse decks and dense chapters never explain; they assume you know what to look for."),("General chatbots are ungrounded.","Fluent, but a student cannot tell an explanation from a plausible invention."),("Plain RAG is still a search box.","It answers what was asked and gives a beginner no way in."),("Benchmarks hide differences.","One stored gold answer per task is arbitrary when many answers are correct.")],size=15)
card(s,0.6,5.5,5.9,1.4,"Our idea","Ground every answer in the course files and let tested code decide how to teach; measure the evaluation, including its reference choice.",size=13)
tb(s,7.0,1.6,6,0.4,"Objectives",size=20,bold=True,color=TEAL)
bullets(s,7.0,2.1,5.8,4.8,[("O1","Index PPTX, PDF and DOCX without silently losing content."),("O2","Compare chunking, retrieval, reranking and prompts on a 26-question golden set; adopt only what measures better."),("O3","Measure the evaluation's own noise so small differences are not over-read."),("O4","Streaming chat: ELI5 / undergrad / exam-prep levels, cited sources."),("O5","Socratic tutor: 30 concepts, 96 graded questions, hint → scaffold → explain, 16 misconception probes, quiz mode, kind handling of struggle and distress."),("O6","Orientation, learning path, starter and follow-up chips for a student who knows nothing."),("O7","Research: measure how much scores, rankings and significance change when only the gold reference is swapped for another valid answer (RCR), and test it on stronger models.")],size=14,gap=6)
notes(s,"Problem: three failure modes of existing options. Our idea: grounding plus a pedagogy layer whose decisions are code. Objectives O1-O3 are the RAG research half; O4-O6 are the tutor half. The prof's focus (Socratic, interactive, friendly, good follow-ups) is O5 and O6. O7 is the research half: many OS answers are equally valid, so a single gold answer is an arbitrary choice; we ask how much that choice matters.")

# 3 methodology
s=prs.slides.add_slide(blank); header(s,"Methodology","The tutoring layer wraps the RAG pipeline on every turn",3)
s.shapes.add_picture(F+"architecture.png",Inches(2.55),Inches(1.35),width=Inches(8.2))
tb(s,0.6,5.55,12.2,0.35,"Chatbot: small-to-big retrieval (match small chunks, read the parent slide)  ·  policy in code (state, grading, next question)  ·  the model only phrases",size=12,bold=True,color=TEAL,align=PP_ALIGN.CENTER)
rect(s,0.6,5.95,12.1,1.0,SOFT); rect(s,0.6,5.95,0.07,1.0,TEAL)
tb(s,0.8,5.98,11.8,0.95,"Research protocol (RCR): 24 executable OS tasks (scheduling, synchronisation, Banker's) · every valid answer V(x) enumerated · three evaluators: E1 exact match, E2 normalised match against ONE reference, E3 validator that replays the answer and never sees a reference · 50,000 sampled reference sets · 4 local models + 4 Claude models (1,152 generations each) · world-level sign-flip test, Holm correction",size=12)
notes(s,"Top: the chatbot architecture. Bottom strip: the research protocol, a separate pipeline that does not use the chatbot. Walk through the red frame first. plan_turn runs before retrieval: triage (distress, off-scope, prompt injection), intent and difficulty detection, grading of the pending question, quiz and orientation. Many turns are answered entirely by authored text chosen by code, with no retrieval and usually no model call. Otherwise the message becomes a RagPlan: dense retrieval over the index (built offline from 36 indexed files: slides chunked into title-prefixed bullet children with the slide as parent, PDFs page-aware), parent expansion capped at 400 tokens, an explain-first teaching prompt, and a streamed local Ollama LLM. finish_rag then appends at most one Socratic question and the follow-up chips. Two optional model calls exist and are validated or clamped: model-written follow-up questions, and one advisory call for free-text answers the regex keys cannot read (at most one level up, never to UNDERSTOOD). Emphasise: the LLM never decides whether a student is right. Everything reaches the browser as SSE events token, ui and sources.")

# 4 R&D 1 RAG
s=prs.slides.add_slide(blank); header(s,"Results & Discussion (1/2): The chatbot, prompt and RAG findings","Measurement overturned the plan: fixing defects and the prompt beat choosing techniques",4)
tb(s,0.5,1.5,4.9,0.35,"Scored prompt (\"few_shot\")",size=15,bold=True,color=TEAL)
rect(s,0.5,1.88,5.0,2.55,RGBColor(0xf0,0xed,0xe6))
code=("Answer the question using only the context\nbelow. If the context doesn't contain the\nanswer, say so.\n\nAnswer in continuous prose, stating each fact\nonce. Do not add preamble about the context.\n\n"
"Example question: What are user mode and\nkernel mode?\nExample answer: CPU hardware has multiple\nprivilege levels: user mode runs user code,\nand kernel mode runs OS code ...\n\nContext: {context}  Question: {query}")
tb(s,0.55,1.9,4.9,2.5,code,size=9.5,font="Courier New")
tb(s,0.5,4.5,5.0,1.5,"Scoring: RAGAS, judge qwen2.5:7b (a different model family from the llama3 generator). Per question the judge sees question, retrieved contexts, answer and ground truth; answer_correctness is an F1 over statements. 26 questions, 5 topics.",size=11.5)
tb(s,0.5,5.95,5.0,1.0,"The app's teaching prompt (explain first; the tutor appends the question) is a different prompt and was not RAGAS-scored.",size=11,color=RED,bold=True)
s.shapes.add_picture(F+"ablation.png",Inches(6.0),Inches(1.4),width=Inches(6.6))
card(s,5.75,5.25,2.3,1.65,"Defects","Titles indexed as chunks: refusals 11.7% → ~0% once fixed.",size=11)
card(s,8.2,5.25,2.3,1.65,"Prompt shape","+0.092 few_shot; CoT −0.059 (answers 27% shorter).",size=11)
card(s,10.65,5.25,2.2,1.65,"Noise ±0.027","Same config scored 0.7752 and 0.7478. Dense R@5 = 1.000.",size=11)
notes(s,"Left: the exact prompt the experiments scored, plus how scores are made. For each of the 26 questions we retrieve contexts and generate an answer, then RAGAS sends the judge the question, contexts, answer and ground truth. The judge splits text into claims and decides entailment; metrics are fractions of those decisions. answer_correctness is an F1 over statements, so answer length and statement granularity move the score. We used a judge from a different family to avoid self-preference bias. Right: read the chart against the shaded band; only bars clearly outside it are results. Defect fixes (+0.111) and the few-shot prompt (+0.092) are real; chain-of-thought hurt because shorter answers state fewer statements. Reranking (+0.029) and multi-query (+0.014) are inside run-to-run noise (same config scored twice: 0.7752 and 0.7478). Important caveat: the teaching prompt students see is not the few_shot prompt, and has no RAGAS score. Other caveats: 26 questions, 7B judge, one run per config, numbers measured on the earlier 22-document corpus, since grown to 36 indexed files.")

# 5 R&D 2 research
s=prs.slides.add_slide(blank); header(s,"Results & Discussion (2/2): Research track (RCR)","Matching one stored answer hides real differences; a validator does not",5)
tb(s,0.5,1.45,4.2,0.35,"The idea in one task",size=15,bold=True,color=TEAL)
rect(s,0.5,1.85,4.2,2.5,RGBColor(0xf0,0xed,0xe6))
tb(s,0.55,1.88,4.1,2.45,"sched_01: FCFS, P1=24, P2=3, P3=3.\nSix orderings are all valid:\n  P1,P2,P3 · P1,P3,P2 · P2,P1,P3\n  P2,P3,P1 · P3,P1,P2 · P3,P2,P1\nStored gold = #1. A model giving #4 is\nequally correct but marked wrong.\nE2 passes a valid answer with probability 1/|V|.\nE[E2] = E3 / |V(x)|  (r = 1.000)",size=10,font="Courier New")
card(s,0.5,4.45,4.2,2.45,"Local models (floor: 6.6-30.9% valid)","Kendall tau-b 0.62 ± 0.35 across 50,000 reference sets. Winner reverses in 17.56% of pairs, but 85.6% of that sits in pairs even the validator cannot separate. The validator finds qwen3 > llama3.1 and > mistral in every draw; E2 detects it in 5 of 50,000 (99.99% missed).",size=11)
tb(s,5.0,1.45,7.8,0.35,"Follow-up: four Claude models above the floor (preregistered)",size=15,bold=True,color=TEAL)
rows=[("Model","Valid","CIF"),("sonnet-5.5","99.3%","3.30"),("haiku-5.5","98.3%","2.67"),("sonnet-4.5","79.9%","2.26"),("haiku-4.5","73.3%","3.11")]
y=1.85
for k,(a,b,c) in enumerate(rows):
    fill=TEAL if k==0 else (SOFT if k%2 else WHITE); col=WHITE if k==0 else INK
    rect(s,5.0,y,3.6,0.36,fill); tb(s,5.05,y+0.02,1.7,0.32,a,size=11,bold=(k==0),color=col); tb(s,6.7,y+0.02,0.9,0.32,b,size=11,bold=(k==0),color=col); tb(s,7.7,y+0.02,0.8,0.32,c,size=11,bold=(k==0),color=col); y+=0.38
tb(s,5.0,3.8,3.6,0.7,"CIF = canonical answer produced ÷ expected under uniform choice among valid answers.",size=10,color=GREY)
hy=[("H1 floor gone","Supported: 4 of 4 above 30%",True),("H2 detection loss","Supported: E2 detects in 3.0% of draws",True),("H3 canonical inflation","Supported: CIF 2.3-3.3 (all > 1)",True),("H4 ranking distortion > 1.5x","NOT supported: max 1.43x",False)]
y=1.85
for a,b,ok in hy:
    rect(s,8.8,y,4.0,0.62,SOFT if ok else RGBColor(0xfb,0xe9,0xe2)); rect(s,8.8,y,0.07,0.62,TEAL if ok else RED)
    tb(s,8.95,y+0.01,3.8,0.3,a,size=11.5,bold=True,color=TEAL if ok else RED); tb(s,8.95,y+0.3,3.8,0.3,b,size=10.5); y+=0.68
card(s,5.0,4.55,3.85,2.35,"Above the floor","Uniform-reference winner reversal rises to 26.9%. Matching k=5 references detects 36-44% of real differences, k=25 detects 51-69%, a single reference only 2-5%.",size=11)
card(s,9.0,4.55,3.85,2.35,"Honest limits","One 24-task domain. Plan is an internal freeze. CLI sampling is provider-default. Metrics defined post hoc. Prevalence of single-reference scoring unaudited. Empirical study, not a proof; workshop-level.",size=11,accent=RED)
notes(s,"Left: the idea. In OS tasks many answers are equally correct, yet a benchmark stores one as gold. We enumerated every valid answer for 24 tasks and varied the gold over 50,000 sampled reference sets, holding model outputs fixed. The validator E3 never sees a reference, so its result is the same by construction; the finding is the cost of not using it. Local models (floor): rankings are unstable (tau-b 0.62, winner reversals 17.56%) but most of that is near-ties; the real loss is detection: E3 finds qwen3 significantly better than two others in every draw while single-reference matching finds it in 5 of 50,000 draws and keeps only 12-18% of the true gap, as the law E[E2]=E3/|V| predicts. Follow-up: to answer the objection that weak models cause this, we froze four hypotheses in writing and ran four Claude models. Three held, one failed: floor gone (73-99% valid), detection loss persists (3.0%), canonical inflation 2.3-3.3 times uniform choice, but the 1.5-fold ranking distortion prediction failed (1.43). H3 caveat: the test that models differ in bias is weak by construction, so only inflation above 1 is claimed. Say clearly: empirical measurement study, one benchmark, internal preregistration, prevalence of single-reference scoring in real benchmarks not audited. The tutor transcript and tests are in the report, section 6.4.")

# 6 conclusion
s=prs.slides.add_slide(blank); header(s,"Conclusion","",6)
card(s,0.6,1.4,3.9,3.5,"What we built","A grounded, streaming OS tutor that explains first, then asks one graded Socratic question (hints, misconception probes, quiz, follow-up chips); and a research study of reference choice on 24 OS tasks with 8 models.",size=14)
card(s,4.7,1.4,3.9,3.5,"What we learned","Chatbot: defects and the prompt beat retrieval technique; measure the noise (±0.027). Research: one stored gold answer hides real model differences (detected in 0.01-3% of draws) and models over-produce the canonical answer 2.3-3.3x; a validator avoids both.",size=14)
card(s,8.8,1.4,4.0,3.5,"Limits and next","26 questions, 7B judge, no learner study. Research: one 24-task domain, internal preregistration, H4 failed, prevalence unaudited. Next: second domain with 65+ tasks, external registration, learner study.",size=14,accent=RED)
rect(s,0.6,5.2,12.2,1.3,SOFT)
tb(s,0.8,5.3,11.8,0.4,"Code, evidence and findings log",size=14,bold=True,color=TEAL)
tb(s,0.8,5.75,11.8,0.5,"github.com/adhyan-jain/OS-Tutor-RAG   (FINDINGS.md · paper/PAPER_FINAL.md = RCR paper)",size=20,bold=True)
notes(s,"Three messages: what exists, what the evidence says, what is not yet proven. The repository link goes to the code and to FINDINGS.md, which records every defect and refuted hypothesis with the measurement behind it. The research track (RCR) is in the report, sections 5.7 and 6.5, and in paper/PAPER_FINAL.md.")

# 7 references
s=prs.slides.add_slide(blank); header(s,"References","",7)
refs=["Lewis et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS 33. arXiv:2005.11401",
"Karpukhin et al. (2020). Dense passage retrieval for open-domain question answering. EMNLP 2020. arXiv:2004.04906",
"Gao et al. (2022). Precise zero-shot dense retrieval without relevance labels (HyDE). arXiv:2212.10496",
"Es et al. (2023). RAGAS: Automated evaluation of retrieval augmented generation. arXiv:2309.15217",
"Zheng et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. arXiv:2306.05685",
"Xiao et al. (2023). C-Pack: Packed Resources For General Chinese Embeddings (BGE). arXiv:2309.07597",
"Wood, Bruner & Ross (1976). The role of tutoring in problem solving. J. Child Psychol. Psychiatry 17(2), 89-100",
"Arpaci-Dusseau & Arpaci-Dusseau. Operating Systems: Three Easy Pieces (course reading)",
"Casola et al. (2025). References Matter: reference set variation in summarization evaluation. INLG 2025. arXiv:2506.14335",
"Jeong et al. (2026). Reporting Practice Matters: reference choice in chest X-ray report evaluation. arXiv:2609.19093",
"Chen et al. (2026). HypoSpace: set-valued hypothesis generation under underdetermination. arXiv:2510.15614 (ICML 2026)",
"OS-Tutor-RAG repository: github.com/adhyan-jain/OS-Tutor-RAG"]
y=1.4
for i,r in enumerate(refs,1):
    tb(s,0.6,y,0.6,0.4,f"[{i}]",size=12,bold=True,color=TEAL); tb(s,1.2,y,11.5,0.45,r,size=12); y+=0.43
tb(s,0.6,6.65,12,0.35,"arXiv identifiers [1]-[6] and [9]-[11] checked against arxiv.org; [7] and [8] are standard journal/textbook citations.",size=11,color=GREY)
notes(s,"arXiv identifiers [1]-[6] were checked against arxiv.org on 2026-10-24; [7] and [8] are standard journal/textbook citations.")
prs.save(SUB+"/OS_Tutor_RAG_Presentation.pptx"); print(len(prs.slides))
