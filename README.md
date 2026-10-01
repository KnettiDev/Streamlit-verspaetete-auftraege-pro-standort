# Verspätete Aufträge pro Standort

Streamlit-Tabelle für die Daten aus `GET /api/v1/verspaetete-auftraege-pro-standort/`.

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Die API muss unter `http://localhost:6001` erreichbar sein. Für eine andere Adresse
die Umgebungsvariable `VERSPAETETE_AUFTRAEGE_API_URL` setzen. Die Daten werden in
einer zentrierten Tabelle angezeigt und 60 Sekunden zwischengespeichert.


