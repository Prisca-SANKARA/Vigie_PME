import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from scanner.engine import perform_scan
from scanner.report import render_report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python src/main.py <domaine>")
        print("Exemple : python src/main.py scanme.nmap.org")
        sys.exit(1)

    hostname, findings = perform_scan(sys.argv[1])
    print(render_report(hostname, findings))
