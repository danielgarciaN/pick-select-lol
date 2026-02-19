from __future__ import annotations

import json

import streamlit as st

from core.db import get_conn, init_db
from core.models import Rule
from core.notes import add_note, add_rule, delete_note, delete_rule, export_rules_json, import_rules_json, list_notes, list_rules

init_db()
st.title("Notes and Rules")

with get_conn() as conn:
    champs = conn.execute("SELECT id, name FROM champions ORDER BY name").fetchall()
champ_options = {f"{r['name']} ({r['id']})": r["id"] for r in champs}

st.header("Notas")
scope = st.selectbox("Scope", ["champion", "role", "general"])
champion_label = st.selectbox("Campeón (opcional)", [""] + list(champ_options.keys()))
role = st.selectbox("Rol (opcional)", ["", "top", "jungle", "mid", "adc", "support"])
text = st.text_area("Nota")
if st.button("Guardar nota") and text.strip():
    add_note(scope=scope, text=text.strip(), champion_id=champ_options.get(champion_label), role=role or None)
    st.success("Nota guardada")

for n in list_notes():
    c = f"champ={n['champion_id']}" if n["champion_id"] else ""
    st.write(f"[{n['id']}] {n['scope']} {c} role={n['role']} :: {n['text']}")
    if st.button(f"Borrar nota {n['id']}"):
        delete_note(n["id"])
        st.rerun()

st.header("Reglas estructuradas")
condition_type = st.selectbox("condition_type", ["enemy_pick", "ally_pick", "role", "team_need", "banned", "mode"])
condition_value = st.text_input("condition_value (champion_id o tag)")
target_type = st.selectbox("target_type", ["champion", "tag"])
target_value = st.text_input("target_value (champion_id o tag)")
weight = st.number_input("weight", value=1.0, step=0.5)
note = st.text_input("note")

if st.button("Guardar regla"):
    rule = Rule(
        condition_type=condition_type,
        condition_value=condition_value,
        target_type=target_type,
        target_value=target_value,
        weight=float(weight),
        note=note or None,
    )
    add_rule(rule)
    st.success("Regla guardada")

for r in list_rules():
    st.write(r.model_dump())
    if st.button(f"Borrar regla {r.id}"):
        delete_rule(int(r.id))
        st.rerun()

st.header("Import / Export JSON")
exported = export_rules_json()
st.download_button("Exportar reglas", data=exported, file_name="rules_export.json")
uploaded = st.file_uploader("Importar JSON", type=["json"])
if uploaded and st.button("Importar"):
    items = json.loads(uploaded.read().decode("utf-8"))
    count = import_rules_json(items)
    st.success(f"Importadas {count} reglas")
