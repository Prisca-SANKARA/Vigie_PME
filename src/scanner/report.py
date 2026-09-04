from datetime import datetime, timezone

from .models import Finding, Severity

SEVERITY_WEIGHT = {
    Severity.INFO: 0,
    Severity.LOW: 2,
    Severity.MEDIUM: 5,
    Severity.HIGH: 10,
    Severity.CRITICAL: 20,
}

SEVERITY_LABEL = {
    Severity.INFO: "INFO",
    Severity.LOW: "FAIBLE",
    Severity.MEDIUM: "MOYEN",
    Severity.HIGH: "ÉLEVÉ",
    Severity.CRITICAL: "CRITIQUE",
}


def compute_score(findings: list[Finding]) -> int:
    penalty = sum(SEVERITY_WEIGHT[f.severity] for f in findings)
    return max(0, 100 - penalty)


def risk_label(score: int) -> str:
    if score >= 90:
        return "Bon niveau de sécurité"
    if score >= 70:
        return "Niveau correct, des points à corriger"
    if score >= 40:
        return "Risque significatif"
    return "Risque critique - action urgente recommandée"


def render_report(target: str, findings: list[Finding]) -> str:
    score = compute_score(findings)
    ordered = sorted(findings, key=lambda f: f.severity.value, reverse=True)

    lines = [
        "=" * 60,
        f"Rapport de sécurité — {target}",
        f"Généré le {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
        f"Score global : {score}/100 — {risk_label(score)}",
        "",
    ]

    if not ordered:
        lines.append("Aucun problème détecté sur les vérifications effectuées.")
        return "\n".join(lines)

    for finding in ordered:
        lines.append(f"[{SEVERITY_LABEL[finding.severity]}] ({finding.category}) {finding.title}")
        lines.append(f"  Détail        : {finding.detail}")
        lines.append(f"  Recommandation: {finding.recommendation}")
        lines.append("")

    return "\n".join(lines)
