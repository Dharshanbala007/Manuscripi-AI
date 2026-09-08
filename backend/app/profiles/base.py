"""PublisherProfile schema. Each rule group records how faithfully it is applied."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class RuleProvenance(StrEnum):
    IMPLEMENTED = "implemented"  # a known official rule, intentionally encoded
    CONFIGURABLE = "configurable"  # sensible default, changeable in the YAML
    INFERRED = "inferred"  # a reasonable value chosen here, not from an official source
    UNSUPPORTED = "unsupported"  # cannot currently be enforced by the engine


class RuleGroup(BaseModel):
    provenance: RuleProvenance = RuleProvenance.INFERRED
    note: str | None = None


class PageRules(RuleGroup):
    size: str = "letter"  # "letter" | "a4"
    margin_top_in: float = 0.75
    margin_bottom_in: float = 1.0
    margin_left_in: float = 0.625
    margin_right_in: float = 0.625


class ColumnRules(RuleGroup):
    count: int = 1
    spacing_in: float = 0.25


class FontRules(RuleGroup):
    family: str = "Times New Roman"
    size_pt: float = 10.0


class SpacingRules(RuleGroup):
    line: float = 1.0
    paragraph_before_pt: float = 0.0
    paragraph_after_pt: float = 0.0


class TitleRules(RuleGroup):
    font_family: str | None = None
    size_pt: float = 24.0
    bold: bool = False
    italic: bool = False
    align: str = "center"
    case: str = "as_is"  # "as_is" | "title" | "upper" | "sentence"


class AuthorRules(RuleGroup):
    size_pt: float = 10.0
    align: str = "center"
    italic: bool = False


class AffiliationRules(RuleGroup):
    size_pt: float = 9.0
    align: str = "center"
    italic: bool = True


class AbstractRules(RuleGroup):
    heading_text: str = "Abstract"
    inline_lead_in: bool = False
    size_pt: float = 9.0
    bold_label: bool = True
    italic_body: bool = False
    align: str = "justify"


class KeywordRules(RuleGroup):
    label: str = "Index Terms"
    size_pt: float = 9.0
    italic: bool = True
    separator: str = ", "


class HeadingLevelRule(BaseModel):
    size_pt: float = 10.0
    bold: bool = False
    italic: bool = False
    align: str = "left"
    case: str = "as_is"
    numbering: str = "none"  # "none" | "decimal" | "roman-upper" | "alpha-upper"
    space_before_pt: float = 6.0
    space_after_pt: float = 3.0


class HeadingRules(RuleGroup):
    levels: dict[int, HeadingLevelRule]


class ParagraphRules(RuleGroup):
    first_line_indent_in: float = 0.2
    align: str = "justify"


class CaptionRule(BaseModel):
    prefix: str = "Fig."
    numbering: str = "decimal"
    separator: str = ". "
    size_pt: float = 8.0
    italic: bool = False
    align: str = "left"
    position: str = "below"  # "below" | "above"
    case: str = "as_is"


class CaptionRules(RuleGroup):
    figure: CaptionRule
    table: CaptionRule


class TableRules(RuleGroup):
    style_name: str = "Table Grid"
    header_bold: bool = True
    max_width_action: str = "flag"  # v1: flag only, never shrink destructively


class FigureRules(RuleGroup):
    max_width_in: float = 3.4
    center: bool = True
    oversize_action: str = "flag"


class ReferenceRules(RuleGroup):
    style: str = "numeric-bracket"
    size_pt: float = 8.0
    hanging_indent_in: float = 0.2
    numbering: str = "bracket"  # "bracket" -> [1]


class ValidationRules(RuleGroup):
    body_font_tolerance_pt: float = 0.5
    require_abstract: bool = True
    require_keywords: bool = True
    max_table_cols_before_flag: int = 8


class PublisherProfile(BaseModel):
    id: str
    name: str
    summary: str
    features: list[str] = []
    status: str = "available"

    page: PageRules
    columns: ColumnRules
    base_font: FontRules
    spacing: SpacingRules
    title: TitleRules
    author: AuthorRules
    affiliation: AffiliationRules
    abstract: AbstractRules
    keywords: KeywordRules
    headings: HeadingRules
    paragraphs: ParagraphRules
    captions: CaptionRules
    tables: TableRules
    figures: FigureRules
    references: ReferenceRules
    validation: ValidationRules

    def rule_groups(self) -> dict[str, RuleGroup]:
        return {name: value for name, value in self if isinstance(value, RuleGroup)}
