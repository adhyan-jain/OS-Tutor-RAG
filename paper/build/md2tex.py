"""
Convert paper/PAPER_FINAL.md to LaTeX (single source of truth stays the Markdown file).

Supports exactly the Markdown subset the manuscript uses: headings, paragraphs,
bold/italic/code spans, inline math \\( \\), display math $$ $$, nested bullet and
numbered lists, block quotes, pipe tables with a preceding '#### Table N: caption'
line, and a numbered References list.

Usage: python paper/build/md2tex.py paper/PAPER_FINAL.md paper/build/PAPER_FINAL.tex
"""

import re
import sys

SPECIAL_TEXT = {
    "τ": r"$\tau$", "≥": r"$\geq$", "≤": r"$\leq$", "×": r"$\times$", "→": r"$\rightarrow$",
    "±": r"$\pm$", "†": r"\textdagger{}", "−": "-", "≈": r"$\approx$", "–": "--", "—": "---",
    "≪": r"$\ll$", "∏": r"$\prod$",
}

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,array}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\setlist{nosep,leftmargin=*}
\sloppy
\emergencystretch=3em
\renewcommand{\arraystretch}{1.15}
"""


def escape_text(s):
    out = []
    for ch in s:
        if ch in SPECIAL_TEXT:
            out.append(SPECIAL_TEXT[ch])
        elif ch == "\\":
            out.append(r"\textbackslash{}")
        elif ch in "&%#_{}":
            out.append("\\" + ch)
        elif ch == "$":
            out.append(r"\$")
        elif ch == "~":
            out.append(r"\textasciitilde{}")
        elif ch == "^":
            out.append(r"\textasciicircum{}")
        else:
            out.append(ch)
    return "".join(out)


def inline(s):
    """Convert inline Markdown (code, math, bold, italic) to LaTeX."""
    holders = []

    def hold(tex):
        holders.append(tex)
        return f"\x00{len(holders) - 1}\x00"

    # code spans first (contents are literal)
    s = re.sub(r"`([^`]+)`", lambda m: hold(r"\texttt{" + escape_text(m.group(1)) + "}"), s)
    # math
    s = re.sub(r"\\\((.+?)\\\)", lambda m: hold("$" + m.group(1) + "$"), s)
    s = escape_text(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: holders[int(m.group(1))], s)
    return s


def is_table_row(line):
    return line.strip().startswith("|") and line.strip().endswith("|")


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_to_tex(rows, caption):
    header = split_row(rows[0])
    aligns = split_row(rows[1])
    body = [split_row(r) for r in rows[2:]]
    spec = "".join("c" if a.startswith(":") and a.endswith(":") else "l" for a in aligns)
    n = len(header)
    out = [r"\begin{table}[htbp]", r"\centering", r"\scriptsize" if n >= 8 else r"\footnotesize",
           r"\setlength{\tabcolsep}{3pt}"]
    if caption:
        out.append(r"\caption{" + inline(caption) + "}")
    out.append(r"\resizebox{\textwidth}{!}{%")
    out.append(r"\begin{tabular}{" + spec + "}")
    out.append(r"\toprule")
    out.append(" & ".join(inline(c) for c in header) + r" \\")
    out.append(r"\midrule")
    for r in body:
        r = r + [""] * (n - len(r))
        out.append(" & ".join(inline(c) for c in r[:n]) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}}")
    out.append(r"\end{table}")
    return "\n".join(out)


def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    title = None
    in_refs = False
    list_stack = []  # entries: (indent, env)
    pending_caption = None

    def close_lists():
        while list_stack:
            out.append(r"\end{" + list_stack.pop()[1] + "}")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            close_lists()
            i += 1
            continue

        # title
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
            i += 1
            continue

        # abstract
        if stripped.startswith("**Abstract**"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            out.append(r"\begin{abstract}")
            out.append(inline(lines[j].strip()))
            out.append(r"\end{abstract}")
            i = j + 1
            continue

        # headings
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            close_lists()
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 4 and text.startswith("Table"):
                pending_caption = re.sub(r"^Table\s+\d+:\s*", "", text)
                i += 1
                continue
            text = re.sub(r"^\d+(\.\d+)*\.?\s+", "", text)
            if level == 2:
                if text.lower().startswith("references"):
                    in_refs = True
                    out.append(r"\section*{" + inline(text) + "}")
                else:
                    out.append(r"\section{" + inline(text) + "}")
            elif level == 3:
                out.append(r"\subsection{" + inline(text) + "}")
            else:
                out.append(r"\paragraph{" + inline(text) + "}")
            i += 1
            continue

        # tables
        if is_table_row(line):
            close_lists()
            rows = []
            while i < len(lines) and is_table_row(lines[i]):
                rows.append(lines[i])
                i += 1
            out.append(table_to_tex(rows, pending_caption))
            pending_caption = None
            continue

        # block quote
        if stripped.startswith(">"):
            close_lists()
            text = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                text.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(r"\begin{quote}" + "\n" + inline(" ".join(text)) + "\n" + r"\end{quote}")
            continue

        # display math on its own line
        dm = re.match(r"^\$\$(.+)\$\$$", stripped)
        if dm:
            out.append(r"\[" + dm.group(1) + r"\]")
            i += 1
            continue

        # lists
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            indent = len(lm.group(1))
            ordered = lm.group(2)[0].isdigit()
            env = "enumerate" if ordered else "itemize"
            while list_stack and list_stack[-1][0] > indent:
                out.append(r"\end{" + list_stack.pop()[1] + "}")
            if not list_stack or list_stack[-1][0] < indent:
                opt = "[label={[\\arabic*]}]" if (ordered and in_refs) else ""
                out.append(r"\begin{" + env + "}" + opt)
                list_stack.append((indent, env))
            out.append(r"\item " + inline(lm.group(3)))
            i += 1
            continue

        # continuation line inside a list item
        if list_stack and line.startswith(" "):
            dm2 = re.match(r"^\$\$(.+)\$\$$", stripped)
            out.append((r"\[" + dm2.group(1) + r"\]") if dm2 else inline(stripped))
            i += 1
            continue

        close_lists()
        if stripped.startswith("†"):
            out.append(r"{\footnotesize " + inline(stripped) + "}")
        else:
            out.append(inline(stripped))
        out.append("")
        i += 1

    close_lists()
    body = "\n".join(out)
    header = PREAMBLE + "\\title{" + inline(title or "") + "}\n\\author{}\n\\date{}\n\\begin{document}\n\\maketitle\n"
    return header + body + "\n\\end{document}\n"


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        tex = convert(f.read())
    with open(dst, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"wrote {dst} ({len(tex.splitlines())} lines)")
