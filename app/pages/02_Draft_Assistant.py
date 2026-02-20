from __future__ import annotations

import json

import streamlit as st

from app.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from core.db import get_conn, init_db
from core.notes import list_rules
from core.recommender import recommend

init_db()
st.title("Draft Assistant")

with get_conn() as conn:
    champs = conn.execute("SELECT id, name FROM champions ORDER BY name").fetchall()
    player = conn.execute("SELECT puuid FROM player ORDER BY last_sync DESC LIMIT 1").fetchone()

champ_options = {f"{r['name']} ({r['id']})": r["id"] for r in champs}

role = st.selectbox("Mi rol", ["top", "jungle", "mid", "adc", "support"])
mode = st.selectbox("Modo", ["blind", "counter"])

ally_picks = st.multiselect("Ally picks", list(champ_options.keys()), max_selections=5)
enemy_picks = st.multiselect("Enemy picks", list(champ_options.keys()), max_selections=5)
ally_bans = st.multiselect("Ally bans", list(champ_options.keys()), max_selections=5)
enemy_bans = st.multiselect("Enemy bans", list(champ_options.keys()), max_selections=5)

ally_ids = [champ_options[x] for x in ally_picks]
enemy_ids = [champ_options[x] for x in enemy_picks]
ally_ban_ids = [champ_options[x] for x in ally_bans]
enemy_ban_ids = [champ_options[x] for x in enemy_bans]

if st.button("Recalcular") or True:
    puuid = player["puuid"] if player else None
    recs = recommend(puuid, role, mode, ally_ids, enemy_ids, ally_ban_ids, enemy_ban_ids, list_rules(), top_k=5)

    st.subheader("Top 5 recomendado")
    id_to_name = {v: k for k, v in champ_options.items()}

    for idx, (champ_id, breakdown) in enumerate(recs, start=1):
        st.markdown(f"### {idx}. {id_to_name.get(champ_id, str(champ_id))} — **{breakdown.total:.2f}**")
        st.write(
            {
                "draft": round(breakdown.draft, 2),
                "personal": round(breakdown.personal, 2),
                "rules": round(breakdown.rules, 2),
                "patch": round(breakdown.patch, 2),
            }
        )
        for reason in breakdown.reasons[:8]:
            st.write(f"- {reason}")

    st.subheader("Alternativos si el #1 cae")
    alts = recommend(puuid, role, mode, ally_ids, enemy_ids, ally_ban_ids + ([recs[0][0]] if recs else []), enemy_ban_ids, list_rules(), top_k=5)
    st.json([{"champion_id": c, "score": b.total} for c, b in alts])

st.caption("Tip: cualquier cambio en picks/bans vuelve a ejecutar automáticamente y actualiza el Top 5.")
