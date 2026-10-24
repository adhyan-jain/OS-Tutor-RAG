import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,"..","figures")+"/"
TEAL="#0f766e"; INK="#1e2128"; SOFT="#e3efec"; PAPER="#faf8f4"; RED="#b3441f"; GREY="#9a9da6"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11})

# 1 ablation
fig,ax=plt.subplots(figsize=(8,4.4),dpi=200)
labels=["Defect fixes\n(chunking, expansion)","Prompt: strict→\nfew-shot","Chain-of-thought\nvs few-shot","Cross-encoder\nreranking","Multi-query","Temperature\n0.2→0.0"]
vals=[0.111,0.092,-0.059,0.029,0.014,-0.013]
cols=[TEAL if abs(v)>0.04 else GREY for v in vals]
ax.axhspan(-0.027,0.027,color=SOFT,zorder=0)
ax.text(5.45,0.031,"noise floor ±0.027",ha="right",va="bottom",color=TEAL,fontsize=9)
b=ax.bar(range(6),vals,color=cols,zorder=2)
for i,v in enumerate(vals): ax.text(i,v+(0.006 if v>=0 else -0.006),f"{v:+.3f}",ha="center",va="bottom" if v>=0 else "top",fontsize=10,color=INK)
ax.axhline(0,color=INK,lw=.8)
ax.set_xticks(range(6)); ax.set_xticklabels(labels,fontsize=8.5)
ax.set_ylabel("Δ answer_correctness"); ax.set_ylim(-0.09,0.14)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.set_title("What moved answer quality (teal: clearly above noise · grey: not established)",fontsize=9.5,color=INK,loc="left")
plt.tight_layout(); plt.savefig(OUT+"ablation.png"); plt.close()

# 2 retrieval
techs=["dense","hyde","dense+\nmulti-query","hybrid_rrf","bm25"]
r1=[0.769,0.654,0.808,0.769,0.654]; r5=[1.0,1.0,0.962,0.923,0.885]; f5=[0.577,0.692,0.577,0.538,0.462]
import numpy as np
x=np.arange(5); w=.26
fig,ax=plt.subplots(figsize=(7.2,4.2),dpi=200)
ax.bar(x-w,r1,w,label="recall@1",color=GREY); ax.bar(x,r5,w,label="recall@5",color=TEAL); ax.bar(x+w,f5,w,label="full@5 (all sources)",color="#2dd4bf")
for xs,vs in ((x-w,r1),(x,r5),(x+w,f5)):
    for a,v in zip(xs,vs): ax.text(a,v+.01,f"{v:.2f}",ha="center",fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(techs,fontsize=9); ax.set_ylim(0,1.12)
ax.legend(frameon=False,fontsize=8.5,ncol=3,loc="upper center",bbox_to_anchor=(.5,1.1))
for s in ("top","right"): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(OUT+"retrieval.png"); plt.close()

# 3 prompts
fig,ax=plt.subplots(figsize=(5.6,3.8),dpi=200)
names=["strict","part_\ncoverage","cot (separate\nrun)","few_shot"]; v=[0.664,0.631,0.689,0.756]
ax.bar(names,v,color=[GREY,RED,GREY,TEAL])
for i,a in enumerate(v): ax.text(i,a+.008,f"{a:.3f}",ha="center",fontsize=10)
ax.set_ylim(0.5,0.8); ax.set_ylabel("answer_correctness")
for s in ("top","right"): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(OUT+"prompts.png"); plt.close()

# 4 architecture: the tutoring layer wraps the RAG pipeline
def box(ax,x,y,w,h,t,fc=SOFT,ec=TEAL,fs=8.6,bold=False,lw=1.4):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=ec,lw=lw))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,color=INK,fontweight="bold" if bold else "normal")
def arr(ax,a,b,c=TEAL,style="-|>",ls="-",rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle=style,mutation_scale=12,color=c,lw=1.4,linestyle=ls,connectionstyle=f"arc3,rad={rad}"))
RS="#fbe9e2"
fig,ax=plt.subplots(figsize=(12.4,6.25),dpi=200); ax.set_xlim(0,12.4); ax.set_ylim(0.35,6.6); ax.axis("off")
# offline strip
ax.text(0.1,6.38,"Offline: build the index",fontsize=9.5,color=TEAL,fontweight="bold")
off=[("Course files\nPPTX · PDF · DOCX",0.1),("Ingest\nslides, pages, tables",2.55),("Chunk\nchild → parent",5.0),("bge-large\n+ FAISS index",7.45)]
for t,x in off: box(ax,x,5.55,2.2,0.7,t,fs=8.4)
for i in range(3): arr(ax,(off[i][1]+2.2,5.9),(off[i+1][1],5.9))
# tutor frame
ax.add_patch(FancyBboxPatch((0.1,0.55),12.2,4.7,boxstyle="round,pad=0.02,rounding_size=0.15",fc="#fffaf7",ec=RED,lw=2,linestyle="--"))
ax.text(0.3,5.0,"TUTORING LAYER (src/tutor)  ·  policy in code, the model only phrases  ·  state per chat: concept states, pending question, quiz, chips seen",fontsize=8.6,color=RED,fontweight="bold")
box(ax,0.3,3.55,1.5,0.95,"Student\nmessage\n(+ Guided\ntoggle)",fs=8.4,fc="white",ec=INK)
box(ax,2.15,3.45,3.1,1.15,"plan_turn  (before retrieval)\ntriage: distress · off-scope · injection\nintent · difficulty · pending-question grading\nquiz · orientation · path",fs=8.2,fc=RS,ec=RED,bold=False)
arr(ax,(1.8,4.02),(2.15,4.02),c=RED)
# code handled
box(ax,2.15,1.45,3.1,1.1,"Authored reply by code\nhint → scaffold → explain, feedback,\nquiz question, path, starter chips\n(0 retrieval, usually 0 model calls)",fs=8,fc=RS,ec=RED)
arr(ax,(3.7,3.45),(3.7,2.55),c=RED); ax.text(3.8,3.0,"handled by code",fontsize=7.6,color=RED)
# RAG pipeline box
ax.add_patch(FancyBboxPatch((5.75,3.15),4.15,1.5,boxstyle="round,pad=0.02,rounding_size=0.1",fc=SOFT,ec=TEAL,lw=1.6))
ax.text(5.9,4.42,"RAG PIPELINE (src)",fontsize=8.6,color=TEAL,fontweight="bold")
names=["Dense\nretrieval","Parent\nexpansion","Teaching\nprompt","Ollama LLM\nstreams"]
xs=[5.88+i*1.0 for i in range(4)]
for n_,x_ in zip(names,xs): box(ax,x_,3.3,0.9,0.85,n_,fs=7.2,fc="white")
for x_ in xs[:3]: arr(ax,(x_+0.9,3.72),(x_+1.0,3.72))
arr(ax,(5.25,4.02),(5.75,4.02),c=TEAL); ax.text(5.28,4.12,"RagPlan",fontsize=7.4,color=TEAL)
arr(ax,(7.45,5.55),(7.0,4.65),c=GREY,ls="--"); ax.text(7.4,5.12,"search",fontsize=7.4,color=GREY)
# finish_rag
box(ax,10.15,3.25,2.0,1.35,"finish_rag\n(after the answer)\none Socratic question\n+ follow-up chips",fs=8.2,fc=RS,ec=RED)
arr(ax,(9.9,3.9),(10.15,3.9))
# optional model
box(ax,5.75,1.45,3.0,1.1,"Optional model calls (validated)\nfollow-up questions written by the\nmodel · one clamped advisory call",fs=8,fc="white",ec=GREY)
arr(ax,(8.75,2.0),(10.4,3.25),c=GREY,ls="--",rad=0.1)
# UI
box(ax,10.15,1.45,2.0,1.1,"UI over SSE\ntoken · ui · sources\nchips, question card,\nprogress pill",fs=8,fc="white",ec=INK)
arr(ax,(11.15,3.25),(11.15,2.55),c=RED)
arr(ax,(3.7,1.45),(11.15,1.45),c=RED,ls="--",rad=0.1)
ax.text(0.3,0.95,"Graded replies are checked by authored regex keys; a model never decides correctness.\nFree-text answers the keys cannot read may get one clamped advisory call (at most 1 level up, never to UNDERSTOOD).",fontsize=8.2,color=INK,va="center")
fig.subplots_adjust(0,0,1,1); plt.savefig(OUT+"architecture.png",facecolor="white"); plt.close()
print("ok")
