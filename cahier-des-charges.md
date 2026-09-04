# Cahier des charges — Vigie_PME (plateforme de cybersécurité mutualisée pour PME)

Auteure : SANKARA P. Djamilatou Prisca
Statut : v1 — document de travail
Dernière mise à jour : 2026-09-04

---

## 1. Contexte et problématique

La grande majorité des PME burkinabè (et ouest-africaines en général) n'ont ni budget ni compétence interne en cybersécurité. Elles restent exposées à des risques basiques et évitables : certificats expirés, ports ouverts inutilement, versions logicielles obsolètes avec vulnérabilités connues, absence de sensibilisation des employés au phishing. Aucune offre locale mutualisée et abordable n'a été identifiée sur ce segment (vérifié par recherche — seuls existent un CIRT national orienté État et une initiative régionale CEDEAO, pas d'offre PME).

## 2. Objectifs

- Donner aux PME un diagnostic de sécurité clair, en français, sans jargon, à un tarif accessible.
- Automatiser la détection des failles les plus courantes et les plus dangereuses (pas l'exhaustivité — la pertinence).
- Sensibiliser les employés (souvent le maillon le plus faible) via des campagnes de phishing simulé.
- Construire un produit qui démontre une expertise DevSecOps de bout en bout : conception, sécurité du produit lui-même, déploiement, automatisation.

## 3. Public cible

- PME locales (10 à 200 employés) ayant un minimum de présence numérique (site web, emails pro, réseau interne).
- Cabinets comptables/juridiques comme revendeurs potentiels auprès de leurs propres clients.
- Cible secondaire (phase ultérieure) : administrations publiques locales.

## 4. Périmètre fonctionnel

### Phase 1 — MVP (à construire en premier)
- Scan externe automatisé et périodique d'un domaine/IP client :
  - ports ouverts, services exposés
  - en-têtes de sécurité HTTP manquants (CSP, HSTS, X-Frame-Options...)
  - état et expiration du certificat SSL/TLS
  - versions logicielles détectables publiquement avec CVE connues
  - fuite de secrets sur des dépôts publics (si le client fournit son org GitHub)
- Rapport lisible en français avec score de risque global et actions priorisées.
- Historique des scans (évolution du score dans le temps).
- Interface web simple pour consulter les rapports (dashboard client).

### Phase 2
- Simulation de campagnes de phishing par email (mesure du taux de clic, formation ciblée après échec).
- Alertes automatiques par email/WhatsApp en cas de nouvelle vulnérabilité critique.
- Comparatif anonymisé sectoriel ("mieux/moins bien sécurisé que X% des PME de votre secteur").

### Phase 3
- Badge public "PME vérifiée cybersécurité" affichable sur le site du client.
- API pour cabinets comptables/revendeurs (gestion multi-clients).
- Extension vers les administrations publiques locales (marché différent, cycle de vente plus long).

### Hors périmètre (explicitement exclu, au moins au départ)
- Tout scan intrusif actif (exploitation de faille) — uniquement de la détection passive/non-intrusive.
- Pentest manuel à la demande (relève d'un service humain, pas de la plateforme).

## 5. Choix techniques — comparaison et justification

### Backend / moteur de scan
| Option | Pour | Contre |
|---|---|---|
| **Python** (recommandé) | Écosystème sécurité très riche (python-nmap, requests, ssl, intégration facile avec Nuclei/testssl.sh en sous-processus), tu as déjà une expérience concrète dessus (projet Cyber Alerte), rapidité de développement | Moins performant que Go sur de très gros volumes concurrents |
| Node.js | Bon pour l'API et le temps réel | Écosystème sécurité offensive moins mature que Python |
| Go | Très performant, agent client léger possible | Courbe d'apprentissage, écosystème sécurité moins riche en bibliothèques prêtes à l'emploi |

**Décision : Python pour le backend et le moteur de scan.** Go reste une option à garder en tête uniquement si un agent client local devient nécessaire en phase 3 (déploiement massif, besoin de performance).

### Outils de scan à réutiliser (ne pas réinventer)
- **Nuclei** (ProjectDiscovery) — scan de vulnérabilités par templates, activement maintenu, très utilisé en pro actuellement.
- **testssl.sh** — audit SSL/TLS de référence.
- **theHarvester** — reconnaissance d'exposition publique (emails, sous-domaines).
- **GoPhish** — simulation de phishing prête à l'emploi (phase 2).
- **Trivy** — scan de vulnérabilités si le client expose des conteneurs.

### Base de données
| Option | Pour | Contre |
|---|---|---|
| **PostgreSQL / Supabase** (recommandé) | Données relationnelles (clients, scans, scores dans le temps), requêtes complexes pour les rapports comparatifs, coût prévisible à l'échelle | Un peu plus de mise en place initiale que Firestore |
| Firebase/Firestore | Rapide à démarrer, tu le maîtrises déjà | Coût imprévisible sur des requêtes fréquentes, moins adapté aux données historiques relationnelles |

**Décision : PostgreSQL via Supabase.** Nature relationnelle des données (historique de scans, scoring) plus adaptée au SQL ; Supabase garde une expérience développeur proche de Firebase pour ne pas perdre trop de vitesse de développement.

### Orchestration des scans périodiques
- **n8n** pour le MVP (scans planifiés, envoi de rapports, alertes) — rapide à mettre en place, visuel, tu voulais explorer cet outil.
- Migration vers Celery + Redis si le volume de clients dépasse ce que n8n peut gérer confortablement.

### Frontend / dashboard client
| Option | Pour | Contre |
|---|---|---|
| HTML/CSS/JS vanilla | Tu maîtrises déjà (ton portfolio) | Moins adapté à un dashboard avec beaucoup de données dynamiques (tableaux, filtres, graphiques) |
| **React** (recommandé pour le dashboard) | Bien plus adapté à une interface data-intensive, compétence très demandée sur le marché | Courbe d'apprentissage si nouveau pour toi |

**Décision : React pour le dashboard client**, en gardant HTML/CSS/JS pour une éventuelle page vitrine publique simple.

### Sécurisation du produit lui-même
- Consentement explicite écrit et vérifiable du client avant tout scan (obligation légale — scanner sans autorisation peut être assimilé à une intrusion).
- Isolation stricte des données par client (pas de fuite croisée entre comptes).
- Chiffrement des rapports au repos.
- Pipeline CI/CD sécurisé pour le déploiement (lien direct avec le projet 2 de ta feuille de route — gitleaks, SAST, scan de dépendances à chaque déploiement).

## 6. Architecture (vue haut niveau)

```
Client (dashboard React) 
   -> API Backend (Python/FastAPI)
        -> Base de données (PostgreSQL/Supabase)
        -> Orchestrateur de scans (n8n)
             -> Modules de scan (Nuclei, testssl.sh, theHarvester...)
        -> Service de notifications (email/WhatsApp)
   -> Déploiement via pipeline CI/CD sécurisé (GitHub Actions + gitleaks + Trivy)
```

## 7. Exigences non fonctionnelles

- **Sécurité** : OWASP Top 10 couvert, rate limiting, authentification forte pour l'accès aux rapports clients.
- **Conformité** : politique de confidentialité claire, minimisation des données collectées, vérifier le cadre légal burkinabè/CEDEAO sur la protection des données.
- **Disponibilité** : suffisante pour un usage non temps-réel (scans périodiques, pas de criticité seconde près).
- **Auditabilité** : journal des scans effectués et des accès aux rapports (traçabilité).

## 8. Modèle économique (résumé)

- Abonnement mensuel B2B par PME, tarif adapté au marché local (en dessous des standards occidentaux).
- Version gratuite limitée (1 scan/mois) pour créer l'usage avant conversion.
- Canal de revente via cabinets comptables/juridiques.

## 9. Jalons proposés

1. **Semaines 1-2** : mise en place du backend Python + intégration Nuclei/testssl.sh en local, scan manuel fonctionnel sur un domaine test.
2. **Semaines 3-4** : base de données, historisation des scans, génération de rapport lisible.
3. **Semaines 5-6** : dashboard React connecté à l'API, authentification client.
4. **Semaines 7-8** : orchestration n8n (scans planifiés + notifications), premier pilote avec 1-2 PME réelles de ton entourage.
5. **Semaines 9-10** : durcissement sécurité du produit + pipeline CI/CD sécurisé pour le déploiement.
6. **Au-delà** : phase 2 (phishing simulé), retours du pilote, itération.

## 10. Critères de succès

- Un scan complet et un rapport compréhensible générés de bout en bout, sans intervention manuelle.
- Au moins 1 à 2 PME réelles utilisant activement la plateforme (preuve d'usage, pas juste une démo).
- Aucune faille critique découverte sur la plateforme elle-même lors d'une auto-revue de sécurité.

## 11. Améliorations possibles, intelligence artificielle et innovations majeures

- **Priorisation intelligente par LLM** : reformuler chaque résultat brut de scan en explication claire + action recommandée, adaptée au niveau technique du client (un patron non-technique ne comprend pas "TLS 1.0 actif", il comprend "vos paiements en ligne peuvent être interceptés").
- **Score de risque prédictif** : au lieu d'un score figé à l'instant du scan, anticiper l'évolution du risque (ex. certificat qui expire dans 20 jours = urgence croissante affichée avant l'échéance).
- **Génération automatique de correctifs simples** : pour les cas basiques (mise à jour de version, ajout d'un en-tête HTTP manquant), proposer voire générer directement le patch/la configuration corrigée.
- **Détection d'anomalies comportementales** (phase avancée, supervision continue) : repérer un trafic ou des connexions inhabituelles pour un client donné, au-delà du scan périodique.
- **Chatbot de support intégré au dashboard**, pour répondre en langage naturel aux questions non-techniques du client ("c'est grave ?", "je fais quoi maintenant ?").
- **Rapport comparatif sectoriel enrichi par IA** : identifier les patterns de vulnérabilités les plus fréquents par secteur d'activité local, pour un argument de vente concret ("70% des commerces en ligne de votre secteur ont ce problème").
- **Badge de confiance dynamique et vérifiable** (QR code renvoyant vers le dernier score validé) — signal marketing réutilisable par la PME cliente sur son propre site.
- **Extension SOC mutualisé** (vision long terme) : passer d'un scan périodique à une supervision quasi continue avec Wazuh, mutualisée entre plusieurs PME pour rester abordable — transforme le produit en embryon de SOC-as-a-service régional.

## 12. Risques identifiés

| Risque | Mitigation |
|---|---|
| Scan perçu comme intrusion sans autorisation claire | Processus de consentement explicite et documenté avant tout scan |
| Faux positifs qui décrédibilisent le rapport | Priorisation contextuelle plutôt que liste brute, validation humaine avant envoi en phase pilote |
| Adoption lente (PME pas sensibilisées à la sécurité) | Version gratuite d'appel, argument concret (exemples réels d'incidents locaux) |
| Charge de modération/interprétation manuelle qui ne scale pas | Automatiser la génération de recommandations en langage clair progressivement |
