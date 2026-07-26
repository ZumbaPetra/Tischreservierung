import streamlit as st
import requests
import json

# =============================================================================
# KONFIGURATION & STYLING
# =============================================================================
st.set_page_config(page_title="Tischreservierung", page_icon="🍽️", layout="centered")

# HIER DEINE GOOGLE APPS SCRIPT WEB APP URL EINTRAGEN
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxHJvsSao9BTE58YTYU6FJ-LDtkM8NPSJnNRgzFepvhyrBPCxm60GpsqBrnIc3_3Syn/exec"

st.caption("Verwalte Reservierungen für Gäste oder nimm Telefonbuchungen direkt auf.")

# =============================================================================
# DATEN LADEN (HOTELS & ZEITEN)
# =============================================================================
@st.cache_data(ttl=60)
def load_hotel_data():
    try:
        response = requests.get(WEB_APP_URL)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    return {
        "Landhotel Knappenberg": {"email": "knappenberg@austria-best-hotels.at", "max_gaeste": 120, "dauer_stunden": 2},
        "Motel Waidhofen": {"email": "waidhofen@austria-best-hotels.at", "max_gaeste": 40, "dauer_stunden": 2},
        "Retz": {"email": "retz@austria-best-hotels.at", "max_gaeste": 40, "dauer_stunden": 2}
    }

hotel_data = load_hotel_data()
# =============================================================================
# FORMULAR UI
# =============================================================================

# 1. Status Auswählen AUSSERHALB des Formulars (für sofortiges Redraw der Felder)
status = st.selectbox("Aktion / Status", ["Neu", "Storno"])
is_storno = (status == "Storno")

with st.form(key="reservation_form"):
    
    # 2. Reservierungsnummer: Nur bei Storno schreibbar
    alte_nummer = st.text_input(
        "Reservierungsnummer (Nur bei Storno nötig)", 
        placeholder="z.B. RES-12345",
        disabled=not is_storno
    )
    
    st.divider()
    
    # 3. Ort / Filiale (Bei Storno deaktiviert)
    hotel_options = list(hotel_data.keys())
    selected_ort = st.selectbox(
        "Ort / Filiale wählen", 
        options=hotel_options,
        disabled=is_storno
    )
    
    # 4. Datum & Uhrzeit (Bei Storno deaktiviert)
    col_datum, col_uhrzeit = st.columns(2)
    with col_datum:
        datum = st.date_input("Datum", disabled=is_storno)
        
    with col_uhrzeit:
        time_slots = [f"{h:02d}:{m:02d}" for h in range(7, 22) for m in (0, 15, 30, 45)]
        uhrzeit = st.selectbox("Uhrzeit", options=time_slots, index=6, disabled=is_storno)

    # 5. Anzahl Personen (Bei Storno deaktiviert)
    personen = st.number_input("Anzahl Personen", min_value=1, max_value=50, value=2, step=1, disabled=is_storno)
    
    # 6. Kontaktdaten (Bei Storno deaktiviert)
    name = st.text_input("Auf Name", placeholder="z.B. Max Mustermann", disabled=is_storno)
    
    col_tel, col_email = st.columns(2)
    with col_tel:
        telefon = st.text_input("Telefonnummer", placeholder="z.B. +4366012345678", disabled=is_storno)
    with col_email:
        email = st.text_input("E-Mail-Adresse", placeholder="z.B. gast@email.com", disabled=is_storno)
        
    # Absende-Button
    submit_button = st.form_submit_button(label="Formular absenden")

# =============================================================================
# VALIDIERUNG & ABSENDEN
# =============================================================================
if submit_button:
    # A) VALIDIERUNG FÜR STORNO
    if is_storno:
        if not alte_nummer.strip():
            st.error("Bitte gib die Reservierungsnummer für die Stornierung ein.")
            st.stop()
            
        payload = {
            "status": "Storno",
            "alte_nummer": alte_nummer.strip()
        }
        
    # B) VALIDIERUNG FÜR NEUE RESERVIERUNG
    else:
        fehlende_felder = []
        if not name.strip():
            fehlende_felder.append("Auf Name")
        if not telefon.strip():
            fehlende_felder.append("Telefonnummer")
        if not email.strip():
            fehlende_felder.append("E-Mail-Adresse")
            
        if fehlende_felder:
            st.error(f"Bitte fülle alle Pflichtfelder aus: {', '.join(fehlende_felder)}")
            st.stop()
            
        payload = {
            "status": "Neu",
            "ort": selected_ort,
            "datum": datum.strftime("%d.%m.%Y"),
            "uhrzeit": uhrzeit,
            "personen": personen,
            "name": name.strip(),
            "telefon": telefon.strip(),
            "email": email.strip()
        }

    # DATEN AN GOOGLE APPS SCRIPT SENDEN
    try:
        with st.spinner("Verarbeite Anfrage..."):
            res = requests.post(WEB_APP_URL, json=payload, headers={"Content-Type": "application/json"})
            result = res.json()
            
            if result.get("erfolg"):
                st.success(result.get("meldung"))
            else:
                st.error(result.get("meldung"))
    except Exception as e:
        st.error(f"Verbindungsfehler: {str(e)}")