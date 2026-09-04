import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scanner.models import Finding, Severity
from scanner.report import compute_score, risk_label


def test_score_perfect_with_no_findings():
    assert compute_score([]) == 100


def test_score_drops_with_critical_finding():
    findings = [
        Finding(category="ssl", severity=Severity.CRITICAL, title="x", detail="x", recommendation="x")
    ]
    assert compute_score(findings) == 80


def test_score_never_goes_below_zero():
    findings = [
        Finding(category="ssl", severity=Severity.CRITICAL, title="x", detail="x", recommendation="x")
        for _ in range(10)
    ]
    assert compute_score(findings) == 0


def test_risk_label_boundaries():
    assert risk_label(100) == "Bon niveau de sécurité"
    assert risk_label(75) == "Niveau correct, des points à corriger"
    assert risk_label(50) == "Risque significatif"
    assert risk_label(10) == "Risque critique - action urgente recommandée"
