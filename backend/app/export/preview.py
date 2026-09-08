"""Structured HTML preview of the manuscript, used when LibreOffice is absent.

Explicitly labelled as structural — never presented as an exact page render.
"""

from __future__ import annotations

import html

from app.domain.elements import ElementType
from app.domain.manuscript import Manuscript
from app.formatting.frontmatter import frontmatter_end

_CSS = """
body{font-family:Georgia,'Times New Roman',serif;max-width:46rem;margin:2rem auto;
padding:0 1rem;color:#1a1a1a;line-height:1.62}
h1{font-size:1.6rem;text-align:center;margin:.2rem 0}
.authors{text-align:center;color:#333}
.aff{text-align:center;font-style:italic;color:#555;font-size:.95rem}
.label{font-weight:700}
.abstract,.kw{font-size:.95rem}
.kw{font-style:italic}
h2{font-size:1.15rem;margin-top:1.7rem}
h3{font-size:1rem;margin-top:1.2rem}
table{border-collapse:collapse;width:100%;margin:.8rem 0}
td{border:1px solid #ccc;padding:.3rem .5rem;font-size:.9rem}
.fig{color:#666;font-style:italic}
.ref{font-size:.85rem;padding-left:1.4rem;text-indent:-1.4rem;margin:.2rem 0}
.note{background:#fff8e1;border:1px solid #ffe082;padding:.6rem .8rem;border-radius:.4rem;
font-size:.85rem;margin-bottom:1.5rem}
"""


def render_structured_html(manuscript: Manuscript, profile_label: str) -> str:
    md = manuscript.metadata
    out: list[str] = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Manuscript preview</title>",
        f"<style>{_CSS}</style></head><body>",
        f"<div class='note'>Structural preview of the {html.escape(profile_label)} format. "
        "Install LibreOffice for an exact page preview of the generated PDF.</div>",
    ]

    if md.title.value:
        out.append(f"<h1>{html.escape(md.title.value)}</h1>")
    if md.authors.value:
        names = ", ".join(a.name for a in md.authors.value)
        out.append(f"<div class='authors'>{html.escape(names)}</div>")
    for aff in md.affiliations:
        out.append(f"<div class='aff'>{html.escape(aff.text)}</div>")
    if md.abstract.value:
        out.append(
            f"<p class='abstract'><span class='label'>Abstract—</span>"
            f"{html.escape(md.abstract.value)}</p>"
        )
    if md.keywords.value:
        out.append(
            f"<p class='kw'><span class='label'>Index Terms—</span>"
            f"{html.escape(', '.join(md.keywords.value))}</p>"
        )

    for block in manuscript.body[frontmatter_end(manuscript.body) :]:
        out.append(_render_block(block))

    out.append("</body></html>")
    return "".join(out)


def _render_block(block) -> str:
    text = html.escape(block.text or "")
    kind = block.kind
    if kind == ElementType.HEADING:
        return f"<h2>{text}</h2>"
    if kind == ElementType.SUBHEADING:
        return f"<h3>{text}</h3>"
    if kind == ElementType.CAPTION:
        return f"<p class='fig'>{text}</p>"
    if kind == ElementType.FIGURE:
        return "<p class='fig'>[figure]</p>"
    if kind == ElementType.EQUATION:
        return "<p class='fig'>[equation]</p>"
    if kind == ElementType.TABLE:
        rows = [r for r in (block.text or "").split("\n") if r.strip()]
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(c.strip())}</td>" for c in r.split("|")) + "</tr>"
            for r in rows
        )
        return f"<table>{body}</table>"
    if kind == ElementType.REFERENCE_ITEM:
        return f"<p class='ref'>{text}</p>"
    if kind in (ElementType.NUMBERED_LIST_ITEM, ElementType.BULLET_LIST_ITEM):
        return f"<p style='padding-left:1.2rem'>{text}</p>"
    return f"<p>{text}</p>"
