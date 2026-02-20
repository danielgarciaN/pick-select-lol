from __future__ import annotations

import streamlit as st

from app.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()
from dotenv import load_dotenv

from core.db import get_conn, init_db
from core.ingest import sync_ddragon, sync_player_and_matches

load_dotenv()
init_db()

st.title("Sync")

summoner = st.text_input("Summoner Name")
tagline = st.text_input("Tagline", value="EUW")
region = st.text_input("Region (platform)", value="euw1")
match_count = st.number_input("N matches", min_value=10, max_value=500, value=200, step=10)

logs: list[str] = []
progress = st.progress(0)
log_box = st.empty()


def log(msg: str) -> None:
    logs.append(msg)
    log_box.code("\n".join(logs))


if st.button("Run Sync"):
    try:
        progress.progress(10)
        sync_ddragon(log)
        progress.progress(40)
        sync_player_and_matches(summoner, tagline, region, int(match_count), log)
        progress.progress(100)
        st.success("Sync completado")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error durante sync: {exc}")

st.subheader("Estado")
with get_conn() as conn:
    counts = {
        "champions": conn.execute("SELECT COUNT(*) c FROM champions").fetchone()["c"],
        "matches": conn.execute("SELECT COUNT(*) c FROM matches").fetchone()["c"],
        "my_participation": conn.execute("SELECT COUNT(*) c FROM my_participation").fetchone()["c"],
        "rules": conn.execute("SELECT COUNT(*) c FROM rules").fetchone()["c"],
    }
st.json(counts)
