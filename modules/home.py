import streamlit as st


def home_page():

    # =========================
    # HERO
    # =========================

    st.markdown("""
    <div style='padding:40px 30px;
    border-radius:24px;
    background:linear-gradient(135deg, rgba(37,99,235,0.18), rgba(220,38,38,0.14), rgba(22,163,74,0.14)), #101827;
    border:1px solid rgba(255,255,255,0.08);
    text-align:center;
    margin-bottom:30px;'>

    <div class='hero-copa' style='font-size:72px;margin-bottom:10px;'>
    🏆
    </div>

    <div class='hero-titulo' style='font-size:64px;font-weight:700;color:white;line-height:1;'>
    POLLA MUNDIAL
    </div>

    <div class='hero-subtitulo' style='font-size:42px;font-weight:700;color:#FACC15;margin-top:8px;'>
    SOMOS 26
    </div>

    <div style='margin-top:20px;font-size:20px;color:#D1D5DB;'>
    Predice. Compite. Gana.
    </div>

    </div>
    """, unsafe_allow_html=True)

    # =========================
    # KPIs
    # =========================

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "💰 Apuesta grupos",
            "$5.000"
        )

    with c2:

        st.metric(
            "🔥 Comisión",
            "10%"
        )

    with c3:

        st.metric(
            "🏆 Jackpot",
            "Acumulado"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # SISTEMA DE PUNTOS
    # =========================

    st.subheader("⭐ Sistema de puntos")

    with st.container(border=True):

        st.markdown("## ✅ MARCADOR EXACTO")

        st.write("## 3 puntos")

    with st.container(border=True):

        st.markdown("## 🟡 RESULTADO (GANADOR/EMPATE)")

        st.write("## 2 puntos")

    with st.container(border=True):

        st.markdown("## ⚪ SOLO POR PARTICIPAR")

        st.write("## 1 punto")

    st.info("""
🏆 En caso de empate en puntos, gana quien tenga más marcadores exactos acertados.
""")

    # =========================
    # EJEMPLOS
    # =========================

    st.subheader("📊 Ejemplos")

    st.table({

        "Predicción": ["2 - 1", "2 - 1", "2 - 1"],

        "Resultado": ["2 - 1", "3 - 1", "1 - 2"],

        "Puntos": ["3", "2", "1"]

    })

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # PREMIOS
    # =========================

    st.subheader("💰 Sistema de premios")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("""
### 🟢 Si hay ganadores

- Se descuenta comisión del 10%
- El resto se divide entre los acertantes
- Cada partido tiene su propio pozo
""")

    with c2:

        st.markdown("""
### 🔥 Si nadie gana

- El premio pasa al JACKPOT (Previo cobro de la comisión)
- El acumulado crece
- Se reparte al final del torneo
""")

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # JACKPOT FINAL
    # =========================

    st.subheader("🏆 Jackpot final")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.success("""
### 🥇 1er lugar

60%
""")

    with c2:

        st.info("""
### 🥈 2do lugar

30%
""")

    with c3:

        st.warning("""
### 🥉 3er lugar

10%
""")

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # VALORES POR FASE
    # =========================

    st.subheader("⚽ Valores por fase")

    st.table({

        "Fase": [

            "Grupos",
            "Octavos",
            "Cuartos",
            "Semifinal",
            "Final"

        ],

        "Valor": [

            "$5.000",
            "$8.000",
            "$10.000",
            "$15.000",
            "$20.000"

        ]

    })

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # REGLA IMPORTANTE
    # =========================

    st.error("""
⏰ Las apuestas se bloquean automáticamente al iniciar cada partido.
""")