"""Regenerate docs/RULES.md from the publisher profile YAML.

Usage:  python scripts/gen_rules_doc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend"))

from app.profiles.loader import load_all_profiles  # noqa: E402
from app.profiles.rules_doc import render_all_rules_md  # noqa: E402


def main() -> None:
    out = _ROOT / "docs" / "RULES.md"
    out.write_text(render_all_rules_md(load_all_profiles()), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(_ROOT)}")


if __name__ == "__main__":
    main()
