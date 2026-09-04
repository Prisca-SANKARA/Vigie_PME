# Vigie_PME

Cybersécurité mutualisée pour PME. Scan de sécurité passif (en-têtes HTTP, certificat SSL/TLS, ports courants exposés), score de risque et recommandations en clair — API FastAPI + dashboard React.

Voir [cahier-des-charges.md](cahier-des-charges.md) pour le contexte complet du projet.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation — scan en ligne de commande

```bash
python src/main.py scanme.nmap.org
```

`scanme.nmap.org` est la cible de test officielle du projet Nmap, prévue pour être scannée librement — c'est la cible utilisée pendant le développement pour ne jamais scanner un domaine sans autorisation.

## Utilisation — API + dashboard

```bash
# Terminal 1 — API (depuis la racine du projet)
uvicorn api.main:app --app-dir src --port 8000

# Terminal 2 — dashboard
cd dashboard
npm install
npm run dev
```

Le dashboard tourne sur `http://localhost:5173`, l'API sur `http://127.0.0.1:8000`.

## Tests

```bash
pytest tests/
```

## Avertissement

Ce scanner n'effectue que des vérifications passives et non intrusives (lecture d'en-têtes, connexion TCP simple). Ne jamais l'utiliser sur un domaine dont vous n'êtes pas propriétaire ou pour lequel vous n'avez pas d'autorisation explicite — voir la section consentement du cahier des charges.
