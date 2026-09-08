"""Render publisher profiles as the human-readable docs/RULES.md tables."""

from __future__ import annotations

from collections.abc import Iterable

from app.profiles.base import PublisherProfile

_HEADER = """# Formatting Rules

This file is generated from the publisher profile YAML by
`scripts/gen_rules_doc.py`. Do not edit it by hand.

Every rule group is tagged with how faithfully the engine applies it:

- **implemented** — a widely-documented official rule, encoded on purpose
- **configurable** — a sensible default you can change in the profile YAML
- **inferred** — a reasonable value chosen for this project, not from an official source
- **unsupported** — the engine cannot currently enforce this
"""

_FOOTER = (
    '> The product never claims a document is "IEEE compliant" or "Springer compliant". '
    'It reports "<profile> format profile applied" and, after validation, '
    '"<profile> validation checks passed" for the checks it actually ran.\n'
)


def render_profile_section(profile: PublisherProfile) -> str:
    lines = [f"## {profile.name} (`{profile.id}`)", "", profile.summary, ""]
    lines.append("| Rule group | Provenance | Key values | Note |")
    lines.append("| --- | --- | --- | --- |")
    for name, group in profile.rule_groups().items():
        dumped = group.model_dump()
        values = ", ".join(f"{k}={v}" for k, v in dumped.items() if k not in ("provenance", "note"))
        note = (dumped.get("note") or "").replace("\n", " ").strip()
        lines.append(f"| `{name}` | {group.provenance} | {_trim(values)} | {note} |")
    return "\n".join(lines) + "\n"


def render_rules_md(profile: PublisherProfile) -> str:
    return render_all_rules_md([profile])


def render_all_rules_md(profiles: Iterable[PublisherProfile]) -> str:
    sections = [_HEADER]
    for profile in profiles:
        sections.append(render_profile_section(profile))
    sections.append(_FOOTER)
    return "\n".join(sections) + "\n"


def _trim(text: str, limit: int = 160) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
