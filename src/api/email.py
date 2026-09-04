import logging
import os

logger = logging.getLogger("vigie_pme.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Handler explicite : sans ça, ce logger hérite du logger racine
    # (niveau WARNING par défaut) et le lien de dev n'apparaît nulle part,
    # silencieusement — piégeux pour un flux "mot de passe oublié".
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

# Aucun fournisseur d'email n'est câblé pour l'instant (pas de compte
# SMTP/SendGrid/Resend configuré). En dev, on logue le lien au lieu de
# l'envoyer, pour ne jamais laisser croire qu'un email a été envoyé alors
# que ce n'est pas le cas.
#
# Pour brancher un vrai envoi en production : définir SMTP_HOST, SMTP_PORT,
# SMTP_USER, SMTP_PASSWORD (ou les variables d'un fournisseur transactionnel
# comme Resend/Brevo) et remplacer le corps de cette fonction par un envoi
# réel. Ne jamais committer de identifiants SMTP en dur dans le code.
SMTP_HOST = os.getenv("SMTP_HOST")


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    if SMTP_HOST:
        raise NotImplementedError(
            "SMTP_HOST est défini mais l'envoi réel n'est pas encore implémenté."
        )

    logger.info("[DEV] Email de réinitialisation pour %s : %s", to_email, reset_link)
