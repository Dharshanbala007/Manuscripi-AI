"""Value types produced by the parser. Deliberately close to OOXML, not yet classified."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.elements import SourceRef


@dataclass
class RunFormat:
    text: str
    font: str | None = None
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False


@dataclass
class ParsedBlock:
    kind_hint: str  # "paragraph" | "table" | "image"
    text: str = ""
    runs: list[RunFormat] = field(default_factory=list)
    style_name: str | None = None
    outline_level: int | None = None  # 0-based: 0 == "Heading 1"
    numbering: str | None = None  # "bullet" | "number" | "list" | None
    alignment: str | None = None  # "left" | "center" | "right" | "justify" | None
    source_ref: SourceRef = field(default_factory=SourceRef)
    has_equation: bool = False
    page_break_before: bool = False
    table_shape: tuple[int, int] | None = None
    image_count: int = 0

    @property
    def max_size_pt(self) -> float | None:
        sizes = [r.size_pt for r in self.runs if r.size_pt is not None]
        return max(sizes) if sizes else None

    @property
    def all_bold(self) -> bool:
        meaningful = [r for r in self.runs if r.text.strip()]
        return bool(meaningful) and all(r.bold for r in meaningful)


@dataclass
class ParsedDocument:
    blocks: list[ParsedBlock] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)
