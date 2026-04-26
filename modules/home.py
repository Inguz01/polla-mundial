import streamlit as st

def home_page():
    st.title("⚽ Polla Mundial")

    st.subheader("Cómo funciona")
    st.markdown("""
    **1. Apuestas por partido**
    - Selecciona los partidos y marca el resultado exacto.
    - Cada apuesta tiene un valor según la fase.
    - Las apuestas se cierran 5 minutos antes del partido.

    **2. Premios por partido**
    - Si aciertas el marcador exacto → ganas.
    - Si hay varios ganadores → se reparte el pozo.
    - Si nadie gana → el dinero va al acumulado (jackpot).

    **3. Ranking (Jackpot)**
    - Cada partido suma puntos.
    - 3 puntos: resultado exacto.
    - 2 puntos: acierto de ganador/empate.
    - 1 punto: participación.

    **4. Premio final**
    - El jackpot se reparte según el ranking final.
    """)

    st.info("🔥 Entre más participes, más opciones tienes de ganar el acumulado.")