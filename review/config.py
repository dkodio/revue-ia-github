"""Lecture de .env sans exécution de commandes ou expansion shell."""
from pathlib import Path
import os


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not key.replace("_", "").isalnum():
            raise ValueError("Ligne .env invalide")
        os.environ.setdefault(key, value.strip().strip("\"'"))


def required(key: str) -> str:
    value = os.environ.get(key, "")
    if not value:
        raise ValueError(f"Variable obligatoire absente : {key}")
    return value
