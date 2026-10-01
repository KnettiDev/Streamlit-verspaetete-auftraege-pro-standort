"""Streamlit report for delayed driving orders by delivery location."""

from __future__ import annotations

import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

import pandas as pd
import streamlit as st


API_URL = os.getenv(
    "VERSPAETETE_AUFTRAEGE_API_URL",
    "http://localhost:6001/api/v1/verspaetete-auftraege-pro-standort/",
)
COLUMNS = {
    "kndnr": "Kundennummer",
    "Kunde": "Kunde",
    "Lieferortnummer": "Lieferortnummer",
    "Lieferort": "Lieferort",
    "AnzFahraufträge": "Anzahl Fahraufträge",
}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_items(url: str) -> list[dict]:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=10) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Die API-Antwort enthält keine 'items'-Liste.")
    return payload["items"]


st.set_page_config(page_title="Verspätete Aufträge pro Standort", layout="wide")
st.markdown(
    """
    <style>
    .block-container { max-width: none; padding: 1.5rem 1rem 2rem; }
    .report-bar { background: #0b4036; color: white; padding: 1rem 1.4rem;
                  font-weight: 700; font-size: 1.1rem; margin: -1.5rem -1rem 1.8rem; }
    h1 { text-align: center; font-weight: 400; font-size: 2rem; margin-bottom: 1.5rem; }
    </style>
    <div class="report-bar">KNETTENBRECH GURDULIC</div>
    """,
    unsafe_allow_html=True,
)
st.title("Verspätete Aufträge pro Standort")

try:
    items = fetch_items(API_URL)
except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
    st.error(f"Daten konnten nicht geladen werden: {exc}")
    st.stop()

frame = pd.DataFrame(items).reindex(columns=COLUMNS).rename(columns=COLUMNS)
frame["Kundennummer"] = frame["Kundennummer"].fillna("").astype(str)
for column in ("Lieferortnummer", "Anzahl Fahraufträge"):
    frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")

st.table(
    frame.style.set_properties(**{"text-align": "center"}).set_table_styles(
        [{"selector": "th", "props": [("text-align", "center")]}]
    ),
    hide_index=True,
)
st.caption(f"{len(frame):,} Datensätzen".replace(",", "."))


