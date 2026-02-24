import streamlit as st
import fastf1
import pandas as pd
import os

# Konfiguracja pamieci podrecznej (cache)
CACHE_DIR = 'f1_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR) 

st.set_page_config(page_title="F1 Smart Predictor", layout="wide")

# Naglowek aplikacji
st.title("System Analityczny Formula 1")
st.markdown("---")

# --- PANEL BOCZNY ---
st.sidebar.header("Parametry wejsciowe")
year = st.sidebar.selectbox("Wybierz sezon", [2025, 2024, 2023], index=0)

@st.cache_data
def get_races(year):
    schedule = fastf1.get_event_schedule(year)
    return schedule[schedule['RoundNumber'] > 0]['EventName'].tolist()

try:
    races = get_races(year)
    selected_race = st.sidebar.selectbox("Wybierz Grand Prix", races)
except Exception as e:
    st.sidebar.error(f"Blad pobierania kalendarza: {e}")
    selected_race = None

# --- GLOWNA LOGIKA ---
if st.sidebar.button("Analizuj wyniki") and selected_race:
    try:
        with st.spinner(f'Przetwarzanie danych dla {selected_race} {year}...'):
            session = fastf1.get_session(year, selected_race, 'R')
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            
            res = session.results[['Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'ClassifiedPosition', 'Points']]
            
            # Konwersja danych na numeryczne
            res['GridPosition'] = pd.to_numeric(res['GridPosition'], errors='coerce')
            res['ClassifiedPosition'] = pd.to_numeric(res['ClassifiedPosition'], errors='coerce')
            res = res.dropna(subset=['GridPosition', 'ClassifiedPosition'])
            
            # Obliczenia
            res['Diff'] = res['GridPosition'] - res['ClassifiedPosition']
            
            # Polskie nazwy dla tabeli
            display_df = res.rename(columns={
                'Abbreviation': 'Skrot',
                'FullName': 'Kierowca',
                'TeamName': 'Zespol',
                'GridPosition': 'Start',
                'ClassifiedPosition': 'Meta',
                'Points': 'Punkty',
                'Diff': 'Bilans'
            })

        # --- WYNIKI ---
        st.subheader(f"Wyniki: {selected_race} {year}")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**Tabela koncowa (Top 10)**")
            st.dataframe(display_df.head(10), use_container_width=True)
        
        with c2:
            st.markdown("**Zysk / Strata pozycji na mecie**")
            st.bar_chart(res.set_index('Abbreviation')['Diff'])

        # --- PROGNOZA ---
        st.markdown("---")
        st.subheader("Algorytm predykcyjny (Alpha)")
        
        res['Score'] = (res['Points'] * 2) + res['Diff']
        top_driver = res.sort_values(by='Score', ascending=False).iloc[0]
        
        st.success(f"Analiza zakonczona pomyslnie")
        st.info(f"""
            **Rekomendacja na kolejny etap:**
            Najwyzszy wskaznik efektywnosci uzyskal: **{top_driver['FullName']}**.
            Obliczony 'Performance Score': **{top_driver['Score']:.1f}**
        """)

        # --- POJEDYNEK KIEROWCOW ---
        st.markdown("---")
        st.subheader("Pojedynek Kierowcow")
        
        all_drivers = res['FullName'].unique()
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            driver1 = st.selectbox("Pierwszy kierowca", all_drivers, index=0)
        with col_p2:
            driver2 = st.selectbox("Drugi kierowca", all_drivers, index=1)
            
        if driver1 and driver2:
            comparison_df = res[res['FullName'].isin([driver1, driver2])]
            comp_table = comparison_df[['FullName', 'TeamName', 'GridPosition', 'ClassifiedPosition', 'Points']].rename(columns={
                'FullName': 'Kierowca', 'TeamName': 'Zespol', 'GridPosition': 'Start', 'ClassifiedPosition': 'Meta', 'Points': 'Punkty'
            })
            st.table(comp_table)
            
            d1_pos = comparison_df[comparison_df['FullName'] == driver1]['ClassifiedPosition'].values[0]
            d2_pos = comparison_df[comparison_df['FullName'] == driver2]['ClassifiedPosition'].values[0]
            winner = driver1 if d1_pos < d2_pos else driver2
            st.write(f"W tym wyscigu lepszy wynik osiagnal: **{winner}**")

    except Exception as e:
        st.error(f"Blad krytyczny: {e}")
else:
    st.info("Wybierz Grand Prix z panelu bocznego i kliknij przycisk 'Analizuj wyniki'.")