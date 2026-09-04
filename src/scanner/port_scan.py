import socket

from .models import Finding, Severity

# Ports courants à vérifier - scan volontairement limité et non intrusif
# (connexion TCP simple, pas de tentative d'exploitation ni de bannière).
COMMON_PORTS = {
    21: ("FTP", Severity.MEDIUM, "FTP transmet les identifiants en clair : migrer vers SFTP/FTPS."),
    22: ("SSH", Severity.INFO, "Port normal si l'accès SSH est volontaire et restreint par IP/clé."),
    23: ("Telnet", Severity.CRITICAL, "Telnet est non chiffré et obsolète : le désactiver et utiliser SSH."),
    25: ("SMTP", Severity.LOW, "Vérifier que le relais SMTP n'est pas ouvert (open relay)."),
    3306: ("MySQL", Severity.HIGH, "Une base de données ne devrait jamais être exposée directement sur Internet."),
    3389: ("RDP", Severity.HIGH, "RDP exposé publiquement est une cible fréquente d'attaques par force brute."),
    5432: ("PostgreSQL", Severity.HIGH, "Une base de données ne devrait jamais être exposée directement sur Internet."),
    6379: ("Redis", Severity.HIGH, "Redis sans authentification exposé publiquement permet un accès direct aux données."),
    8080: ("HTTP alternatif", Severity.LOW, "Vérifier qu'un service de test/admin n'est pas oublié en accès public."),
}


def scan_ports(hostname: str, timeout: float = 1.5) -> list[Finding]:
    """Scan TCP connect non intrusif sur un ensemble restreint de ports courants."""
    findings: list[Finding] = []

    for port, (service, severity, recommendation) in COMMON_PORTS.items():
        if _is_port_open(hostname, port, timeout):
            findings.append(
                Finding(
                    category="ports",
                    severity=severity,
                    title=f"Port {port} ouvert ({service})",
                    detail=f"{hostname} répond sur le port {port} ({service}).",
                    recommendation=recommendation,
                )
            )

    return findings


def _is_port_open(hostname: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except OSError:
        return False
