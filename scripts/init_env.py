"""Prépare .env sans écraser les réglages existants."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env existe déjà. Aucun changement.")
content = (root / ".env.example").read_text(encoding="utf-8")
content = content.replace("OPENPROJECT_SECRET_KEY_BASE=\n", "OPENPROJECT_SECRET_KEY_BASE=" + secrets.token_hex(64) + "\n")
target.write_text(content, encoding="utf-8")
target.chmod(0o600)
print(".env créé. Renseignez les jetons après la création des comptes.")
