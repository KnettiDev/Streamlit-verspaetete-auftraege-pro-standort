"""Streamlit report for delayed driving orders by delivery location."""

from __future__ import annotations

import io
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
    "Kunde": "Kunde",
    "kndnr": "Kundennummer",
    "Lieferort": "Lieferort",
    "Lieferortnummer": "Lieferortnummer",
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


def to_excel(frame: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Verspätete Aufträge")
        sheet = writer.sheets["Verspätete Aufträge"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            width = min(65, max(15, *(len(str(cell.value or "")) + 2 for cell in column)))
            sheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()


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

toolbar_left, toolbar_right = st.columns([3, 2], vertical_alignment="bottom")
with toolbar_left:
    st.download_button(
        "Excel-Export",
        data=to_excel(frame),
        file_name="verspaetete-auftraege-pro-standort.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
with toolbar_right:
    search = st.text_input("Suchen", placeholder="Kunde, Lieferort oder Nummer suchen")

if search.strip():
    matches = frame.fillna("").astype(str).apply(
        lambda column: column.str.contains(search.strip(), case=False, regex=False)
    )
    visible = frame.loc[matches.any(axis=1)]
else:
    visible = frame

st.dataframe(
    visible,
    hide_index=True,
    use_container_width=True,
    height=min(720, max(180, (len(visible) + 1) * 35)),
    column_config={
        "Kundennummer": st.column_config.TextColumn("Kundennummer", width="small"),
        "Kunde": st.column_config.TextColumn("Kunde", width="medium"),
        "Lieferort": st.column_config.TextColumn("Lieferort", width="large"),
        "Lieferortnummer": st.column_config.NumberColumn("Lieferortnummer", format="%d"),
        "Anzahl Fahraufträge": st.column_config.NumberColumn("Anzahl Fahraufträge", format="%d"),
    },
)
st.caption(f"{len(visible):,} von {len(frame):,} Datensätzen".replace(",", "."))
