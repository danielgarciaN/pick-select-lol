# Draft Assistant LoL (MVP)

Asistente de draft para League of Legends con UI en Streamlit y motor de recomendación **interpretable**.

## Qué hace

- Sincroniza datos de Riot API + Data Dragon.
- Guarda todo en SQLite local.
- Permite introducir picks/bans manualmente en tiempo real.
- Recalcula al instante el **Top 5** recomendado.
- Incluye notas y reglas personalizadas con pesos.
- Explica cada recomendación con desglose determinístico (sin LLM).

## Stack

- Python 3.11+
- Streamlit
- SQLite
- requests
- pydantic
- python-dotenv

## Configuración rápida

1. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Crear `.env` en la raíz:

```env
RIOT_API_KEY=RGAPI-xxxx
RIOT_REGION=euw1
RIOT_ROUTING=europe
DB_PATH=./data/draft_assistant.db
```

- `RIOT_REGION` = platform routing (ej: `euw1`, `na1`, `la1`), usado en Summoner-V4 y Champion-Mastery-V4.
- `RIOT_ROUTING` = regional routing (ej: `europe`, `americas`, `asia`), usado en Account-V1 y Match-V5.

## Ejecutar app

```bash
streamlit run app/Home.py
```

## Flujo recomendado

1. Ir a **Sync**:
   - introduce `summonerName`, `tagline`, `region`.
   - pulsa sincronizar para bajar:
     - versión de Data Dragon
     - campeones
     - PUUID
     - mastery
     - últimas partidas (N, por defecto 200)
2. Ir a **Notes and Rules**:
   - crear notas por campeón o rol
   - crear reglas estructuradas
   - importar/exportar reglas JSON
3. Ir a **Draft Assistant**:
   - seleccionar rol y modo
   - añadir picks/bans manualmente
   - ver Top 5 + explicaciones

## Reglas estructuradas

Campos de cada regla:

- `condition_type`: `enemy_pick`, `ally_pick`, `role`, `team_need`, `banned`, `mode`
- `condition_value`: champion_id o tag/valor semántico
- `target_type`: `champion` o `tag`
- `target_value`: champion_id o tag
- `weight`: float
- `note`: opcional

Ejemplos en `data/rules_examples.json`.

## Motor de scoring (MVP)

```text
score_total =
  W_DRAFT * score_draft
+ W_PERSONAL * score_personal
+ W_NOTES * score_rules
+ W_PATCH * score_patch
```

Por defecto:

- `W_DRAFT = 0.62` (máximo peso)
- `W_PERSONAL = 0.23`
- `W_NOTES = 0.14`
- `W_PATCH = 0.01`

### score_draft
- sinergia con aliados (matriz editable)
- counters contra enemigos (matriz editable)
- necesidades de composición (`engage`, `frontline`, `ap`, `ad`, `peel`, `waveclear`)
- exclusión por bans / picks ya usados

### score_personal
- winrate suavizado (prior bayesiano)
- KDA proxy suavizado
- recency penalty (si no lo juegas en N días)
- mastery bonus (log-scale)

### score_rules
- aplica reglas que hagan match con estado de draft
- targets por campeón o por tag

### score_patch
- MVP: neutro (0), pero el módulo está preparado para extender.

## Matrices y tags editables

- `data/synergy_matrix.json`
- `data/counter_matrix.json`
- `data/manual_tags.json`

## Tests

```bash
pytest -q
```

Incluye tests unitarios para:
- parseo de campeones Data Dragon
- aplicación de reglas
- scoring de draft

## Troubleshooting

- **401/403 de Riot API**: revisa `RIOT_API_KEY` temporal y región/routing correctos.
- **429 rate limit**: el cliente implementa backoff/retry + caché local + no re-ingestión de `match_id` existente.
- **No aparecen campeones**: ejecuta Sync y verifica `latest_version` en DB.
- **SQLite bloqueado**: cierra otras instancias de la app y reintenta.

## Estructura

```text
app/
  Home.py
  pages/
    01_Sync.py
    02_Draft_Assistant.py
    03_Notes_and_Rules.py
    04_Settings_Debug.py
core/
  riot_client.py
  ddragon.py
  db.py
  models.py
  ingest.py
  features.py
  draft_engine.py
  recommender.py
  notes.py
  utils_cache.py
data/
  manual_tags.json
  synergy_matrix.json
  counter_matrix.json
  rules_examples.json
tests/
```
