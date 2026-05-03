import streamlit as st


def home_page():

    st.title("Bienvenido a la Polla Mundial")

    st.subheader("Reglas del juego")

    st.markdown("""
## 🧠 Sistema de puntos

Cada partido otorga puntos así:

- ✅ **Marcador exacto** → 3 puntos  
- 🟡 **Resultado correcto (ganador o empate)** → 2 puntos  
- ⚪ **Participación** → 1 punto  

### 📌 Ejemplos

| Predicción | Resultado real | Puntos |
|----------|---------------|--------|
| 2 - 1 | 2 - 1 | **3** |
| 2 - 1 | 3 - 1 | **2** |
| 2 - 1 | 1 - 2 | **1** |

👉 En caso de empate en puntos:  
Se define por **mayor número de aciertos exactos**

---

## 💰 Premios por partido

- Cada partido genera un **pozo independiente**
- El valor depende de la fase
- Se descuenta una comisión del **10%**
- El resto se reparte entre quienes acierten el marcador exacto

---

## 💰 Ejemplo real

Supongamos:

- 10 jugadores  
- Valor apuesta: **$5.000**

### 📊 Resultado:

- 💵 Pozo bruto: **$50.000**
- 🧾 Comisión (10%): **$5.000**
- 🎯 Pozo a repartir: **$45.000**

---

### 🟢 Caso 1: Hay ganadores (3 personas)

- Cada uno recibe:  
👉 **$15.000**

---

### 🔴 Caso 2: NO hay ganadores

👉 Los **$45.000** pasan al **JACKPOT**

---

## 🏆 Premio final (Jackpot)

El acumulado se reparte así:

- 🥇 1er lugar → **60%**  
- 🥈 2do lugar → **30%**  
- 🥉 3er lugar → **10%**

---

## ⚙️ Valores por fase

| Fase | Valor |
|------|------|
| Grupos | $5.000 |
| Octavos | $8.000 |
| Cuartos | $10.000 |
| Semifinal | $15.000 |
| Final | $20.000 |

""")