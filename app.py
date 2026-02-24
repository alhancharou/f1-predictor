import streamlit as st
import fastf1
import pandas as pd
import os

# Konfiguracja pamięci podręcznej (cache)
CACHE_DIR = 'f1_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR) 

# Ustawienia strony
st.set_page_config(page_title="F1 Smart Predictor", layout="wide")

st.title("System Analityczny Formula 1 v1.1")

# --- PANEL BOCZNY (SIDEBAR) ---
st.sidebar.header("Ustawienia")
year = st.sidebar.selectbox("Sezon", [2025, 2024, 2023, 2022, 2021, 2020], index=0)

# Funkcja pobierająca kalendarz wyścigów
@st.cache_data
def get_races(year):
    schedule = fastf1.get_event_schedule(year)
    # Pobieramy tylko te wydarzenia, które są wyścigami (RoundNumber > 0)
    return schedule[schedule['RoundNumber'] > 0]['EventName'].tolist()

races = get_races(year)
selected_race = st.sidebar.selectbox("Wybierz Grand Prix", races)

# --- GŁÓWNA LOGIKA PROGRAMU ---
if st.sidebar.button("Uruchom analizę"):
    try:
        with st.spinner(f'Pobieranie i przetwarzanie danych dla {selected_race}...'):
            # Pobieranie danych sesji wyścigowej
            session = fastf1.get_session(year, selected_race, 'R')
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            
            # Wybór kluczowych kolumn
            res = session.results[['Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'ClassifiedPosition', 'Points']]
            
            # Konwersja danych na format numeryczny (obsługa błędów typu 'R' dla DNF)
            res['GridPosition'] = pd.to_numeric(res['GridPosition'], errors='coerce')
            res['ClassifiedPosition'] = pd.to_numeric(res['ClassifiedPosition'], errors='coerce')
            
            # Usuwamy kierowców, którzy nie zostali sklasyfikowani
            res = res.dropna(subset=['GridPosition', 'ClassifiedPosition'])
            
            # Obliczanie zmiany pozycji (awans/spadek)
            res['Zmiana'] = res['GridPosition'] - res['ClassifiedPosition']

            # Zmiana nazw kolumn dla lepszej czytelności w tabeli
            display_df = res.rename(columns={
                'Abbreviation': 'Skrót',
                'FullName': 'Kierowca',
                'TeamName': 'Zespół',
                'GridPosition': 'Start',
                'ClassifiedPosition': 'Meta',
                'Points': 'Punkty'
            })

        # --- WIZUALIZACJA DANYCH ---
        st.subheader(f"Analiza etapu: {selected_race} {year}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Tabela wyników (Top 10)**")
            st.dataframe(display_df.head(10), use_container_width=True)
        
        with col2:
            st.write("**Efektywność (Zysk/Strata pozycji)**")
            # Wykres słupkowy zmiany pozycji
            st.bar_chart(res.set_index('Abbreviation')['Zmiana'])

        # --- SEKCJA PREDYKCJI (Predictive Analytics) ---
        st.markdown("---")
        st.subheader("Analityka predykcyjna")
        
        # Algorytm "Współczynnik Formy": (Punkty + 1) / Pozycja na mecie
        res['Współczynnik_Formy'] = (res['Points'] * 0.8) + (res['Zmiana'] * 2.0)
        
        best_predict = res.sort_values(by='Współczynnik_Formy', ascending=False).iloc[0]
        
        st.success(f"Dane zostały pomyślnie przetworzone!")
        
        st.info(f"""
            **Prognoza na następny wyścig:**
            Na podstawie analizy wydajności (Współczynnik Formy), faworytem jest: **{best_predict['FullName']}**.
            Obliczony wskaźnik efektywności: **{best_predict['Współczynnik_Formy']:.2f}**
        """)
        
        st.caption("Model predykcyjny bazuje na stosunku zdobytych punktów do zajętej pozycji. Wersja rozwojowa będzie uwzględniać średnią z 3 ostatnich wyścigów.")

    except Exception as e:
        st.error(f"Wystąpił błąd podczas ładowania danych: {e}")
else:
    st.info("Wybierz Grand Prix z panelu bocznego i kliknij przycisk 'Uruchom analizę'.")