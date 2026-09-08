from pathlib import Path

import pytest

from app.profiles.base import RuleProvenance
from app.profiles.loader import ProfileNotFound, list_profiles, load_profile
from app.profiles.rules_doc import render_rules_md

_RULES_MD = Path(__file__).parents[3] / "docs" / "RULES.md"


def test_ieee_profile_loads_with_expected_values():
    p = load_profile("ieee")
    assert p.id == "ieee"
    assert p.columns.count == 2
    assert p.base_font.family == "Times New Roman"
    assert p.base_font.size_pt == 10.0
    assert set(p.headings.levels) == {1, 2, 3}
    assert p.headings.levels[1].numbering == "roman-upper"


def test_every_rule_group_has_valid_provenance():
    p = load_profile("ieee")
    groups = p.rule_groups()
    assert groups  # non-empty
    for group in groups.values():
        assert group.provenance in set(RuleProvenance)


def test_unknown_profile_raises():
    with pytest.raises(ProfileNotFound):
        load_profile("does-not-exist")


def test_list_profiles_marks_springer_planned():
    by_id = {s.id: s for s in list_profiles()}
    assert by_id["ieee"].status == "available"
    assert by_id["springer"].status == "planned"


def test_rules_doc_covers_every_group():
    p = load_profile("ieee")
    rendered = render_rules_md(p)
    text = _RULES_MD.read_text(encoding="utf-8") if _RULES_MD.exists() else ""
    for key in p.rule_groups():
        assert f"`{key}`" in rendered
        assert key in text, f"docs/RULES.md is missing '{key}'; run scripts/gen_rules_doc.py"
