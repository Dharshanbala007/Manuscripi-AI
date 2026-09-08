from app.domain.issues import Issue, IssueCategory, Severity
from app.validation.health import CATEGORY_WEIGHTS, score


def test_no_issues_is_full_health():
    result = score([])
    assert result.total == 100
    assert all(v == 100 for v in result.categories.values())
    assert set(result.categories) == set(CATEGORY_WEIGHTS)
    assert result.contributors == []


def test_single_structure_error_reduces_total_and_category():
    issue = Issue(
        id="val-no-title",
        severity=Severity.ERROR,
        category=IssueCategory.STRUCTURE,
        message="The manuscript has no title.",
    )
    result = score([issue])
    assert result.categories["Structure"] == 75
    assert result.total < 100
    assert result.total == round(100 * 0.8 + 75 * 0.2)
    assert result.contributors and result.contributors[0].category == "Structure"


def test_metadata_issue_hits_metadata_category():
    issue = Issue(
        id="meta-title-lowconf",
        severity=Severity.INFO,
        category=IssueCategory.STRUCTURE,
        message="Title detection is uncertain.",
    )
    result = score([issue])
    assert result.categories["Metadata"] < 100
    assert result.categories["Structure"] == 100


def test_score_is_deterministic():
    issues = [
        Issue(
            id="fig-x-nocap",
            severity=Severity.WARNING,
            category=IssueCategory.LAYOUT,
            message="no caption",
        ),
        Issue(
            id="ref-gaps",
            severity=Severity.WARNING,
            category=IssueCategory.REFERENCES,
            message="gap",
        ),
    ]
    assert score(issues).__dict__ == score(issues).__dict__


def test_category_deduction_is_capped():
    many = [
        Issue(id=f"e{i}", severity=Severity.ERROR, category=IssueCategory.FORMATTING, message="x")
        for i in range(10)
    ]
    assert score(many).categories["Formatting"] == 40  # 100 - capped 60
