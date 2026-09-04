import requests

from .models import Finding, Severity

# (header name, severity if missing, recommendation)
SECURITY_HEADERS = [
    (
        "Strict-Transport-Security",
        Severity.HIGH,
        "Ajouter 'Strict-Transport-Security: max-age=31536000; includeSubDomains' pour forcer HTTPS.",
    ),
    (
        "Content-Security-Policy",
        Severity.MEDIUM,
        "Définir une Content-Security-Policy pour limiter les sources de scripts/styles autorisées (protection XSS).",
    ),
    (
        "X-Content-Type-Options",
        Severity.LOW,
        "Ajouter 'X-Content-Type-Options: nosniff' pour empêcher le navigateur de deviner le type MIME.",
    ),
    (
        "X-Frame-Options",
        Severity.MEDIUM,
        "Ajouter 'X-Frame-Options: DENY' ou une CSP frame-ancestors pour empêcher le clickjacking.",
    ),
    (
        "Referrer-Policy",
        Severity.LOW,
        "Ajouter 'Referrer-Policy: strict-origin-when-cross-origin' pour limiter les fuites d'URL.",
    ),
    (
        "Permissions-Policy",
        Severity.LOW,
        "Ajouter une Permissions-Policy pour désactiver les API navigateur non utilisées (caméra, micro, géoloc...).",
    ),
]


def scan_headers(url: str, timeout: int = 10) -> list[Finding]:
    """Vérifie la présence des en-têtes de sécurité HTTP recommandés sur `url`."""
    findings: list[Finding] = []

    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        return [
            Finding(
                category="headers",
                severity=Severity.INFO,
                title="Site inaccessible",
                detail=f"Impossible de joindre {url} : {exc}",
                recommendation="Vérifier que l'URL est correcte et que le site est en ligne.",
            )
        ]

    present_headers = {h.lower() for h in response.headers.keys()}

    for header_name, severity, recommendation in SECURITY_HEADERS:
        if header_name.lower() not in present_headers:
            findings.append(
                Finding(
                    category="headers",
                    severity=severity,
                    title=f"En-tête manquant : {header_name}",
                    detail=f"La réponse de {url} ne contient pas l'en-tête {header_name}.",
                    recommendation=recommendation,
                )
            )

    if response.url.startswith("http://"):
        findings.append(
            Finding(
                category="headers",
                severity=Severity.HIGH,
                title="Site accessible en HTTP non chiffré",
                detail=f"{url} répond en HTTP sans redirection automatique vers HTTPS.",
                recommendation="Forcer une redirection systématique de HTTP vers HTTPS côté serveur.",
            )
        )

    return findings
