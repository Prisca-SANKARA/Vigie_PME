from urllib.parse import urlparse

from .headers import scan_headers
from .models import Finding
from .port_scan import scan_ports
from .ssl_check import scan_ssl


def perform_scan(target: str) -> tuple[str, list[Finding]]:
    """Lance le scan complet (headers + SSL + ports) sur `target` (domaine ou URL).

    Retourne (hostname, findings) — pas de rendu texte ici, pour rester
    réutilisable aussi bien par la CLI que par l'API.
    """
    hostname = urlparse(target).hostname or target
    url = target if target.startswith("http") else f"https://{target}"

    findings: list[Finding] = []
    findings += scan_headers(url)
    findings += scan_ssl(hostname)
    findings += scan_ports(hostname)

    return hostname, findings
