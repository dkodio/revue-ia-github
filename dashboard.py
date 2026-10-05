"""Tableau de bord local en lecture seule, optionnel."""
from pathlib import Path
import os
import sqlite3
import streamlit as st

st.set_page_config(page_title="Revues de code", layout="wide")
st.title("Suivi des revues de code")
st.write("Les recommandations assistent la décision humaine. Elles ne mesurent pas le nombre réel de défauts.")
root = Path(os.environ.get("REVIEWS_DIR", str(Path(__file__).parent / "runs")))
db_path = root.resolve() / "history.sqlite3"
if not db_path.exists():
    st.info("Aucune revue disponible. Exécutez d'abord la démonstration ou une revue réelle.")
    st.stop()
show_demo = st.checkbox("Inclure les démonstrations simulées", value=False)
with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
    db.row_factory = sqlite3.Row
    rows = [dict(r) for r in db.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT 1000")]
rows = [r for r in rows if show_demo or not r["demo"]]
repos = sorted({r["repository"] for r in rows})
repo = st.selectbox("Dépôt", ["Tous"] + repos)
if repo != "Tous":
    rows = [r for r in rows if r["repository"] == repo]
left, middle, right = st.columns(3)
left.metric("Revues affichées", len(rows))
middle.metric("Avec corrections recommandées", sum(r["decision"] == "corrections_recommandees" for r in rows))
right.metric("PR distinctes", len({(r["repository"], r["pr"]) for r in rows}))
st.dataframe(rows, hide_index=True)
st.caption("Au maximum 1 000 exécutions récentes. Réactualiser la page pour charger les nouvelles revues.")
