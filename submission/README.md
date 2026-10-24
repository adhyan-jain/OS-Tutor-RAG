# Submission files

- `OS_Tutor_RAG_Report.docx` / `.pdf` - 21-page report (title page, ToC, Introduction, Literature Review (5 papers), Problem Statement, Objectives, Methodology, Results & Discussion incl. prompts, evaluation and a real tutor transcript, Conclusion with GitHub link, Limitations, Future Work, References).
- `OS_Tutor_RAG_Presentation.pptx` / `.pdf` - exactly 7 slides with speaker notes (Title, Intro & Objective, Methodology/architecture with the tutor layer around the RAG pipeline, R&D 1 = prompt + RAG findings, R&D 2 = the tutor in action + how it was checked, Conclusion, References).
- `figures/` - charts and the architecture diagram used in both.
- `build/` - everything needed to rebuild: `build.sh` (runs all steps), `transcript.py` (drives the real `src.tutor.engine`, no models), `figs.py`, `report.py`, `ppt.py`, `toc.py`.
  Rebuild: `python3 -m venv /tmp/subvenv && /tmp/subvenv/bin/pip install python-docx python-pptx matplotlib pillow`, then `VENV=/tmp/subvenv bash submission/build/build.sh` (needs LibreOffice and poppler).

## Fill in before submitting
- `[COURSE NAME]` - title page of both files (course code BCSE307P and faculty Dr. Jagalingam are filled in)
- `[SLOT]`, `[SEMESTER]` - report title page
- VIT logo - placeholder text on the report title page and slide 1

Both files now cover the OS Tutor chatbot and the Reference-Choice Robustness research (report sections 2.7, 5.7, 6.5; slides 3 and 5).
