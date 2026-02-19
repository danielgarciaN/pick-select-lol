from __future__ import annotations

import os

import streamlit as st

from core.db import get_conn, get_db_path, get_state, init_db

init_db()
st.title("Settings & Debug")

st.write({
    "DB_PATH": str(get_db_path()),
    "RIOT_REGION": os.getenv("RIOT_REGION"),
    "RIOT_ROUTING": os.getenv("RIOT_ROUTING"),
    "API_KEY_SET": bool(os.getenv("RIOT_API_KEY")),
    "latest_version": get_state("latest_version"),
})

with get_conn() as conn:
    sample = conn.execute("SELECT * FROM champions ORDER BY name LIMIT 10").fetchall()
st.dataframe([dict(r) for r in sample])
