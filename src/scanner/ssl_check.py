import socket
import ssl
from datetime import datetime, timezone

from .models import Finding, Severity

EXPIRY_WARNING_DAYS = 30


def scan_ssl(hostname: str, port: int = 443, timeout: int = 10) -> list[Finding]:
    """Vérifie le certificat SSL/TLS et la version de protocole négociée sur hostname:port."""
    findings: list[Finding] = []
    context = ssl.create_default_context()

    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
                tls_version = tls_sock.version()
    except (socket.timeout, socket.gaierror, ConnectionRefusedError) as exc:
        return [
            Finding(
                category="ssl",
                severity=Severity.INFO,
                title="Connexion HTTPS impossible",
                detail=f"Impossible de se connecter à {hostname}:{port} : {exc}",
                recommendation="Vérifier que le port 443 est ouvert et que le serveur accepte les connexions TLS.",
            )
        ]
    except ssl.SSLCertVerificationError as exc:
        return [
            Finding(
                category="ssl",
                severity=Severity.CRITICAL,
                title="Certificat SSL invalide",
                detail=f"Le certificat de {hostname} n'a pas pu être vérifié : {exc}",
                recommendation="Installer un certificat valide signé par une autorité de confiance (ex. Let's Encrypt).",
            )
        ]

    findings.extend(_check_expiry(hostname, cert))
    findings.extend(_check_tls_version(hostname, tls_version))

    return findings


def _check_expiry(hostname: str, cert: dict) -> list[Finding]:
    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )
    days_left = (not_after - datetime.now(timezone.utc)).days

    if days_left < 0:
        severity = Severity.CRITICAL
        title = "Certificat SSL expiré"
    elif days_left <= EXPIRY_WARNING_DAYS:
        severity = Severity.HIGH
        title = f"Certificat SSL bientôt expiré ({days_left} jours restants)"
    else:
        return []

    return [
        Finding(
            category="ssl",
            severity=severity,
            title=title,
            detail=f"Le certificat de {hostname} expire le {not_after.date().isoformat()}.",
            recommendation="Renouveler le certificat, idéalement via un renouvellement automatique (ex. certbot).",
        )
    ]


def _check_tls_version(hostname: str, tls_version: str) -> list[Finding]:
    outdated = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.1"}
    if tls_version in outdated:
        return [
            Finding(
                category="ssl",
                severity=Severity.HIGH,
                title=f"Version TLS obsolète négociée : {tls_version}",
                detail=f"{hostname} accepte encore des connexions en {tls_version}, considéré comme non sûr.",
                recommendation="Désactiver les versions TLS < 1.2 côté serveur, ne garder que TLS 1.2 et 1.3.",
            )
        ]
    return []
