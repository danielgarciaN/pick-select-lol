from __future__ import annotations

import streamlit as st

from app.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from core.db import init_db

st.set_page_config(page_title="LoL Draft Assistant", layout="wide")
init_db()

st.title("LoL Draft Assistant (MVP)")
st.write("Asistente de draft en tiempo real con scoring interpretable.")

st.markdown(
    """
### Navegación
- **Sync**: sincroniza Riot API + Data Dragon.
- **Draft Assistant**: picks/bans manuales y Top 5.
- **Notes and Rules**: notas y reglas personalizadas.
- **Settings & Debug**: revisar DB y estado.
"""
)
