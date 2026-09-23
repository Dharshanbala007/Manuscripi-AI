# Formatting Rules

This file is generated from the publisher profile YAML by
`scripts/gen_rules_doc.py`. Do not edit it by hand.

Every rule group is tagged with how faithfully the engine applies it:

- **implemented** — a widely-documented official rule, encoded on purpose
- **configurable** — a sensible default you can change in the profile YAML
- **inferred** — a reasonable value chosen for this project, not from an official source
- **unsupported** — the engine cannot currently enforce this

## IEEE (`ieee`)

Two-column academic layout with structured headings and IEEE-style references.

| Rule group | Provenance | Key values | Note |
| --- | --- | --- | --- |
| `page` | implemented | size=letter, margin_top_in=0.75, margin_bottom_in=1.0, margin_left_in=0.625, margin_right_in=0.625 | US Letter with IEEE conference margins. |
| `columns` | implemented | count=2, spacing_in=0.25 | IEEE conference papers are two-column. |
| `base_font` | implemented | family=Times New Roman, size_pt=10.0 | 10 pt Times New Roman body text. |
| `spacing` | inferred | line=1.0, paragraph_before_pt=0.0, paragraph_after_pt=0.0 | Single line spacing; exact lead values are not encoded. |
| `title` | inferred | font_family=None, size_pt=24.0, bold=False, italic=False, align=center, case=as_is | Centered ~24 pt; the official template value is approximate here. |
| `author` | inferred | size_pt=10.0, align=center, italic=False | Centered author block below the title. |
| `affiliation` | inferred | size_pt=9.0, align=center, italic=True | Centered italic affiliation lines. |
| `abstract` | implemented | heading_text=Abstract, inline_lead_in=True, size_pt=9.0, bold_label=True, italic_body=False, align=justify | Bold 'Abstract—' run-in lead-in; 9 pt body. |
| `keywords` | implemented | label=Index Terms, size_pt=9.0, italic=True, separator=,  | 'Index Terms—' italic run-in block. |
| `headings` | implemented | levels={1: {'size_pt': 10.0, 'bold': False, 'italic': False, 'align': 'center', 'case': 'upper', 'numbering': 'roman-upper', 'space_before_pt': 12.0, 'space_af… | Level 1 uppercase, centered, roman-numeral numbered; level 2 italic title-case with letter numbering; level 3 italic run-in. Run-in rendering (level 3 inline with the paragraph) is not applied by the engine. |
| `paragraphs` | inferred | first_line_indent_in=0.2, align=justify | First-line indent; justified body. |
| `captions` | implemented | figure={'prefix': 'Fig.', 'numbering': 'decimal', 'separator': '. ', 'size_pt': 8.0, 'italic': False, 'align': 'left', 'position': 'below', 'case': 'as_is'}, t… | Figure captions read "Fig. N." below the figure; table captions read "TABLE N" above the table. Small-caps table titles are not applied. |
| `tables` | configurable | style_name=Table Grid, header_bold=True | Grid style with a bold header row; a table wider than the column is scaled down to fit (columns keep their proportions, text just wraps). Tables with too many columns to stay readable at that width are flagged instead. |
| `figures` | configurable | max_width_in=3.4, center=True, oversize_action=flag | Centered, single-column width; oversize figures are flagged, never scaled. |
| `references` | implemented | style=numeric-bracket, size_pt=8.0, hanging_indent_in=0.2, numbering=bracket | 8 pt, bracketed [n] numbering with a hanging indent. |
| `validation` | configurable | body_font_tolerance_pt=0.75, require_abstract=True, require_keywords=True, max_table_cols_before_flag=8 | Thresholds the validator uses when checking the formatted output. |

## Springer (`springer`)

Single-column A4 layout with decimal-numbered headings and structured references.

| Rule group | Provenance | Key values | Note |
| --- | --- | --- | --- |
| `page` | inferred | size=a4, margin_top_in=1.0, margin_bottom_in=1.0, margin_left_in=1.0, margin_right_in=1.0 | A4 with ~1 in (2.5 cm) margins - a common Springer starting point, not a template value. |
| `columns` | inferred | count=1, spacing_in=0.0 | Single column - the common case for Springer journal and LNCS body text. |
| `base_font` | inferred | family=Times New Roman, size_pt=10.0 | 10 pt serif. Real Springer templates use a bespoke serif; Times New Roman stands in. |
| `spacing` | inferred | line=1.0, paragraph_before_pt=0.0, paragraph_after_pt=0.0 | Single line spacing; exact lead values are not encoded. |
| `title` | inferred | font_family=None, size_pt=15.0, bold=True, italic=False, align=center, case=as_is | Centered, larger than body, bold. |
| `author` | inferred | size_pt=10.0, align=center, italic=False | Centered author line below the title. |
| `affiliation` | inferred | size_pt=9.0, align=center, italic=True | Centered italic affiliation lines. |
| `abstract` | inferred | heading_text=Abstract, inline_lead_in=False, size_pt=9.0, bold_label=False, italic_body=False, align=justify | 'Abstract' as a heading (not a run-in lead-in); slightly smaller, justified. |
| `keywords` | inferred | label=Keywords, size_pt=9.0, italic=False, separator=,  | 'Keywords' label, not italicised. |
| `headings` | configurable | levels={1: {'size_pt': 12.0, 'bold': True, 'italic': False, 'align': 'left', 'case': 'as_is', 'numbering': 'decimal', 'space_before_pt': 12.0, 'space_after_pt'… | Decimal numbering (1, 1.1, 1.1.1) is a documented Springer convention, but the engine does not inject the numbering prefixes - only typography, weight, and spacing are applied. Sizes are inferred. |
| `paragraphs` | inferred | first_line_indent_in=0.2, align=justify | First-line indent; justified body. |
| `captions` | inferred | figure={'prefix': 'Fig.', 'numbering': 'decimal', 'separator': '. ', 'size_pt': 9.0, 'italic': False, 'align': 'left', 'position': 'below', 'case': 'as_is'}, t… | "Fig. N" below the figure; "Table N" above the table; ~9 pt. |
| `tables` | configurable | style_name=Table Grid, header_bold=True | Grid style with a bold header row; a table wider than the column is scaled down to fit (columns keep their proportions, text just wraps). Tables with too many columns to stay readable at that width are flagged instead. |
| `figures` | configurable | max_width_in=5.5, center=True, oversize_action=flag | Centered, single-page width; oversize figures are flagged, never scaled. |
| `references` | configurable | style=numeric-bracket, size_pt=9.0, hanging_indent_in=0.25, numbering=bracket | Bracketed [n] numbering with a hanging indent. Author-year is the other common Springer style and is not implemented. |
| `validation` | configurable | body_font_tolerance_pt=0.75, require_abstract=True, require_keywords=True, max_table_cols_before_flag=10 | Thresholds the validator uses when checking the formatted output. |

> The product never claims a document is "IEEE compliant" or "Springer compliant". It reports "<profile> format profile applied" and, after validation, "<profile> validation checks passed" for the checks it actually ran.

