"""Tutoring layer on top of the RAG pipeline.

The RAG pipeline (``src.pipeline``) decides *what the course material says*.
This package decides *how a tutor behaves*: which concept a student is on,
whether they understand it, which short Socratic question to ask next, when to
give a hint or the answer, and which follow-up questions to offer a student who
does not yet know what to ask.

Design rule carried over from the LabTutor project: policy lives in code, not in
a prompt. Everything here that decides (concept detection, answer grading,
state transitions, which question or chip comes next) is deterministic and
tested; a model only ever *phrases* an outcome, and the single place it may
advise (``realise``) is clamped.
"""
