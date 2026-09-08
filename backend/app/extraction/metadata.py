"""Heuristic metadata detection. Pure functions over ParsedBlocks; no I/O.

Every returned Field carries a confidence in [0, 1]. The caller decides what a
low score means (flag for review); this module never fabricates content.
"""

from __future__ import annotations

import re
import statistics

from app.domain.manuscript import Affiliation, Author, Field, Metadata
from app.parsing.blocks import ParsedBlock

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

_KEYWORDS_RE = re.compile(
    r"^\s*(keywords|key\s*words|index\s*terms)\s*[:—\-]?\s*(.+)$", re.IGNORECASE
)
_ABSTRACT_LABEL_RE = re.compile(r"^\s*abstract\s*$", re.IGNORECASE)
_ABSTRACT_INLINE_RE = re.compile(r"^\s*abstract\s*[—:.\-]\s*(.+)$", re.IGNORECASE | re.DOTALL)
_SECTION_LABEL_RE = re.compile(
    r"^\s*(abstract|keywords|key\s*words|index\s*terms|introduction|"
    r"\d+\.?\s+introduction)\b",
    re.IGNORECASE,
)
_ORG_RE = re.compile(
    r"\b(univ|universit|institut|department|dept\.?|laborator|labs?|college|academy|"
    r"school of|centre|center for|gmbh|inc\.?|ltd\.?|corporation)\b",
    re.IGNORECASE,
)
_SUP_MARKERS = "*†‡§¶∗"
_NAME_CHARS_RE = re.compile(r"[A-Za-z.\-'À-ɏ ]+")

# ponytail: hand-tuned weights; adjust against sample_documents if precision drifts.
_TITLE_WEIGHTS = {
    "first": 0.18,
    "size": 0.22,
    "bold": 0.12,
    "center": 0.18,
    "length": 0.14,
    "noperiod": 0.06,
    "style": 0.10,
}
_TITLE_SCAN = 6
_AUTHOR_WINDOW = 5


def extract_metadata(blocks: list[ParsedBlock], confidence_threshold: float = 0.6) -> Metadata:
    md = Metadata.empty()
    paras = [b for b in blocks if b.kind_hint in ("paragraph", "image") and b.text.strip()]
    if not paras:
        return md

    median_size = _median_run_size(blocks)
    max_size = _max_run_size(blocks)

    title_idx, title_conf = _detect_title(paras, median_size, max_size)
    if title_idx is not None:
        tb = paras[title_idx]
        md.title = Field(
            value=tb.text.strip(), confidence=round(title_conf, 3), source_ref=tb.source_ref
        )

    authors, affiliations, authors_conf, authors_ref = _detect_authors(
        paras, title_idx, confidence_threshold
    )
    md.authors = Field(value=authors, confidence=round(authors_conf, 3), source_ref=authors_ref)
    md.affiliations = affiliations

    abstract_value, abstract_conf, abstract_ref = _detect_abstract(blocks)
    md.abstract = Field(
        value=abstract_value, confidence=round(abstract_conf, 3), source_ref=abstract_ref
    )

    kw_value, kw_conf, kw_ref = _detect_keywords(blocks)
    md.keywords = Field(value=kw_value, confidence=round(kw_conf, 3), source_ref=kw_ref)

    _attach_emails(md, blocks)
    return md


# --- title ------------------------------------------------------------------


def _detect_title(
    paras: list[ParsedBlock], median_size: float | None, max_size: float | None
) -> tuple[int | None, float]:
    best_idx: int | None = None
    best = 0.0
    for i, b in enumerate(paras[:_TITLE_SCAN]):
        text = b.text.strip()
        if _SECTION_LABEL_RE.match(text):
            continue
        words = text.split()
        s_first = 1.0 if i == 0 else 0.5 if i == 1 else 0.15
        s_size = _size_signal(b.max_size_pt, median_size, max_size)
        s_bold = 1.0 if b.all_bold else 0.0
        s_center = 1.0 if b.alignment == "center" else 0.0
        n = len(words)
        s_len = 1.0 if 3 <= n <= 18 else 0.4 if 19 <= n <= 30 else 0.0
        s_noperiod = 0.0 if text.rstrip().endswith((".", ";", ":")) else 1.0
        style = (b.style_name or "").lower()
        s_style = 1.0 if style == "title" else 0.6 if style.startswith("heading 1") else 0.0

        score = (
            _TITLE_WEIGHTS["first"] * s_first
            + _TITLE_WEIGHTS["size"] * s_size
            + _TITLE_WEIGHTS["bold"] * s_bold
            + _TITLE_WEIGHTS["center"] * s_center
            + _TITLE_WEIGHTS["length"] * s_len
            + _TITLE_WEIGHTS["noperiod"] * s_noperiod
            + _TITLE_WEIGHTS["style"] * s_style
        )
        if EMAIL_RE.search(text):
            score *= 0.3
        if _ORG_RE.search(text):
            score *= 0.5

        if score > best:
            best, best_idx = score, i
    return best_idx, best


def _size_signal(
    block_size: float | None, median_size: float | None, max_size: float | None
) -> float:
    if block_size is None:
        return 0.3
    if max_size is not None and block_size >= max_size - 0.01:
        return 1.0
    if median_size and block_size >= median_size * 1.3:
        return 0.6
    return 0.0


# --- authors / affiliations ----------------------------------------------------


def _detect_authors(
    paras: list[ParsedBlock], title_idx: int | None, threshold: float
) -> tuple[list[Author], list[Affiliation], float, object | None]:
    if title_idx is None:
        return [], [], 0.0, None

    authors: list[Author] = []
    affiliations: list[Affiliation] = []
    ref = None
    best_conf = 0.0

    for offset in range(1, _AUTHOR_WINDOW):
        idx = title_idx + offset
        if idx >= len(paras):
            break
        b = paras[idx]
        text = b.text.strip()
        if not text:
            continue
        if _SECTION_LABEL_RE.match(text) or b.outline_level is not None:
            break
        if _ORG_RE.search(text):
            affiliations.append(
                Affiliation(id=f"aff{len(affiliations) + 1}", text=text, confidence=0.7)
            )
            continue
        if EMAIL_RE.search(text) and len(text.split()) <= 2:
            continue

        names = [n for n in _split_names(text) if _looks_like_name(n)]
        if names:
            line_conf = _author_line_confidence(text, first_line=(offset == 1), n_names=len(names))
            if line_conf >= threshold * 0.5:
                if ref is None:
                    ref = b.source_ref
                best_conf = max(best_conf, line_conf)
                authors.extend(Author(name=n, confidence=round(line_conf, 3)) for n in names)
                continue

        if authors or affiliations:
            break

    return authors, affiliations, best_conf, ref


def _split_names(text: str) -> list[str]:
    parts = re.split(r"\s*,\s*|\s+and\s+|\s*&\s*|\s*;\s*", text)
    out = []
    for part in parts:
        p = part.strip().strip(_SUP_MARKERS).strip()
        p = re.sub(r"[\s,]*[\d\*†‡]+$", "", p).strip()
        p = re.sub(r"^[\d\*†‡]+\s*", "", p).strip()
        if p:
            out.append(p)
    return out


def _looks_like_name(s: str) -> bool:
    if not s or len(s) > 60 or _ORG_RE.search(s) or EMAIL_RE.search(s):
        return False
    tokens = s.split()
    if not 1 <= len(tokens) <= 5:
        return False
    if not _NAME_CHARS_RE.fullmatch(s):
        return False
    caps = sum(1 for t in tokens if t[:1].isupper())
    return caps >= max(1, len(tokens) - 1)


def _author_line_confidence(text: str, *, first_line: bool, n_names: int) -> float:
    c = 0.4
    if first_line:
        c += 0.3
    low = text.lower()
    if "," in text or " and " in low or "&" in text:
        c += 0.15
    if not text.rstrip().endswith(".") and len(text.split()) < 25:
        c += 0.15
    if _ORG_RE.search(text):
        c -= 0.4
    if n_names == 0:
        c -= 0.5
    return max(0.0, min(1.0, c))


# --- abstract / keywords -----------------------------------------------------


def _detect_abstract(blocks: list[ParsedBlock]) -> tuple[str, float, object | None]:
    for i, b in enumerate(blocks):
        text = b.text.strip()
        if not _ABSTRACT_LABEL_RE.match(text):
            continue
        collected: list[str] = []
        for nb in blocks[i + 1 :]:
            nt = nb.text.strip()
            if not nt:
                continue
            if (
                nb.outline_level is not None
                or nb.kind_hint == "table"
                or _SECTION_LABEL_RE.match(nt)
                or _KEYWORDS_RE.match(nt)
            ):
                break
            collected.append(nt)
            if len(collected) >= 3:
                break
        if collected:
            return " ".join(collected), 0.9, b.source_ref

    for b in blocks:
        m = _ABSTRACT_INLINE_RE.match(b.text.strip())
        if m and len(m.group(1).split()) >= 15:
            return m.group(1).strip(), 0.75, b.source_ref

    return "", 0.0, None


def _detect_keywords(blocks: list[ParsedBlock]) -> tuple[list[str], float, object | None]:
    for b in blocks:
        m = _KEYWORDS_RE.match(b.text.strip())
        if not m:
            continue
        parts = [p.strip(" .;·") for p in re.split(r"[,;·]", m.group(2))]
        parts = [p for p in parts if p]
        if parts:
            return parts, 0.9, b.source_ref
    return [], 0.0, None


def _attach_emails(md: Metadata, blocks: list[ParsedBlock]) -> None:
    emails: list[str] = []
    for b in blocks[:12]:
        emails.extend(EMAIL_RE.findall(b.text))
    authors = md.authors.value
    if not emails or not authors:
        return
    if len(emails) == len(authors):
        for author, email in zip(authors, emails, strict=False):
            author.email = email
    else:
        authors[0].email = emails[0]


# --- misc ------------------------------------------------------------------


def _run_sizes(blocks: list[ParsedBlock]) -> list[float]:
    return [r.size_pt for b in blocks for r in b.runs if r.size_pt is not None]


def _median_run_size(blocks: list[ParsedBlock]) -> float | None:
    sizes = _run_sizes(blocks)
    return statistics.median(sizes) if sizes else None


def _max_run_size(blocks: list[ParsedBlock]) -> float | None:
    sizes = _run_sizes(blocks)
    return max(sizes) if sizes else None
