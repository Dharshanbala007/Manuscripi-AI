"""Map heading text to a canonical academic section, and build the outline tree."""

from __future__ import annotations

import re

from app.domain.elements import Block, ElementType, SectionNode

# canonical key -> accepted heading phrasings (lowercased, prefix-stripped)
SECTION_SYNONYMS: dict[str, list[str]] = {
    "introduction": ["introduction", "background", "overview", "motivation"],
    "related_work": [
        "related work",
        "literature review",
        "prior work",
        "state of the art",
        "related literature",
    ],
    "methods": [
        "methods",
        "method",
        "methodology",
        "materials and methods",
        "materials & methods",
        "experimental setup",
        "experimental design",
        "study design",
        "approach",
        "proposed method",
        "proposed approach",
    ],
    "results": ["results", "findings", "experiments", "experimental results", "evaluation"],
    "discussion": ["discussion", "discussion and analysis"],
    "conclusion": [
        "conclusion",
        "conclusions",
        "concluding remarks",
        "summary and conclusion",
        "summary and conclusions",
        "future work",
    ],
    "references": ["references", "bibliography", "works cited", "literature cited"],
    "appendix": ["appendix", "appendices", "supplementary material", "supplementary materials"],
    "acknowledgement": [
        "acknowledgement",
        "acknowledgements",
        "acknowledgment",
        "acknowledgments",
    ],
}

_NUM_PREFIX_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?|[ivxlcdm]+\.|[a-z]\.)\s+", re.IGNORECASE)


def canonicalize_heading(text: str) -> str | None:
    cleaned = _NUM_PREFIX_RE.sub("", text or "").strip().strip(":.").lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return None
    for canon, variants in SECTION_SYNONYMS.items():
        if cleaned in variants:
            return canon
    for canon, variants in SECTION_SYNONYMS.items():
        for variant in variants:
            if variant in cleaned and len(cleaned) <= len(variant) + 12:
                return canon
    return None


def build_outline(blocks: list[Block]) -> list[SectionNode]:
    roots: list[SectionNode] = []
    stack: list[tuple[int, SectionNode]] = []
    for b in blocks:
        if b.kind not in (ElementType.HEADING, ElementType.SUBHEADING):
            continue
        level = b.level or 1
        node = SectionNode(
            id=f"sec-{b.id}",
            label=b.text.strip(),
            level=level,
            block_id=b.id,
            canonical=b.section,
        )
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1].children.append(node)
        else:
            roots.append(node)
        stack.append((level, node))
    return roots
