import streamlit as st
import numpy as np
import pandas as pd

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(page_title="What-If Simulator - Fuga de Cerebros", page_icon="🛫", layout="wide")

st.title("🛫 Simulador 'What-If' macroeconómico: Fuga de Cerebros")
st.markdown("---")

# ==============================================================================
# 2. PANEL LATERAL: CONTROLES MACROECONÓMICOS
# ==============================================================================
st.sidebar.header("🔧 Parámetros del Escenario (Horizonte 2030)")

# Sliders interactivos basados en los rangos reales del TFM
brecha = st.sidebar.slider("Brecha Salarial por Hora con la UE (€/h)", 
                           min_value=-25.0, max_value=0.0, value=-12.5, step=0.5)

inversion_id = st.sidebar.slider("Inversión en I+D (% del PIB)", 
                                  min_value=1.1, max_value=3.0, value=1.4, step=0.05)

paro_juvenil = st.sidebar.slider("Tasa de Paro Juvenil (%)", 
                                  min_value=15.0, max_value=55.0, value=25.0, step=0.5)

st.sidebar.markdown("---")

# ==============================================================================
# 3. PANEL LATERAL: SELECCIÓN Y DESCRIPCIÓN DINÁMICA DEL MODELO
# ==============================================================================
st.sidebar.header("🧠 Configuración del Modelo")

tipo_modelo = st.sidebar.radio(
    "Selecciona el enfoque del motor predictivo:",
    ("Modelo de Simulación Teórica (Signos Corregidos)", "Modelo Estadístico Puro (OLS Histórico)")
)

st.sidebar.markdown("---")

# Textos descriptivos de la barra lateral que cambian según el radio button
if tipo_modelo == "Modelo de Simulación Teórica (Signos Corregidos)":
    st.sidebar.subheader("📋 Lógica Económica")
    st.sidebar.write(
        "Este modo **corrige la dirección** del Paro y del I+D basándose en las teorías "
        "de Becker y Massey. Al mover las barras, un aumento de la inversión en ciencia "
        "**retiene talento** (resta stock), y un aumento del paro **expulsa profesionales** (suma stock)."
    )
else:
    st.sidebar.subheader("📋 Lógica Estadística")
    st.sidebar.write(
        "Este modo ejecuta los coeficientes **MCO puros** extraídos de Python (2014-2023). "
        "Refleja el comportamiento histórico real, donde debido a la inercia temporal corta ($n=10$), "
        "el I+D y el Paro muestran signos invertidos por coincidencia de tendencias."
    )

# ==============================================================================
# 4. MOTOR MATEMÁTICO: LÓGICA DE LOS COEFICIENTES (AJUSTE DE SIGNOS)
# ==============================================================================
# Coeficientes base extraídos de la regresión OLS del TFM
intercepto = -110897.0
beta_brecha = -22448.73

if tipo_modelo == "Modelo de Simulación Teórica (Signos Corregidos)":
    # Modificamos el intercepto base para estabilizar la escala en el entorno de las proyecciones
    intercepto_sim = 217400.0 
    # Invertimos los signos para que sigan la lógica push-pull teórica
    beta_id = -35000.0   # Más I+D -> MENOS emigración (Retención)
    beta_paro = 1200.0   # Más paro -> MÁS emigración (Expulsión)
    
    # Cálculo dinámico basado en desviaciones sobre el escenario base neutro
    stock_predicho = intercepto_sim + (beta_brecha * (brecha + 12.5)) + (beta_id * (inversion_id - 1.4)) + (beta_paro * (paro_juvenil - 25.0))
else:
    # Coeficientes matemáticos puros (Con efectos de inercia temporal)
    beta_id = 37248.86
    beta_paro = -572.57
    stock_predicho = intercepto + (beta_brecha * brecha) + (beta_id * inversion_id) + (beta_paro * paro_juvenil)

# Forzamos límite inferior por coherencia de datos (No pueden existir emigrantes negativos)
if stock_predicho < 0:
    stock_predicho = 0

# ==============================================================================
# 5. VISUALIZACIÓN PRINCIPAL DE RESULTADOS (SIN RECUADROS VACÍOS)
# ==============================================================================
st.subheader("📊 Resultado de la Simulación")

# Mostramos la métrica de forma limpia a lo ancho de la página principal
st.metric(
    label="Stock Estimado para 2030", 
    value=f"{int(stock_predicho):,} profesionales"
)

# Mostramos el cuadro de evaluación del entorno justo debajo
if stock_predicho > 250000:
    st.error("🚨 Escenario de Riesgo Alto: Fuga de talento masiva por precarización estructural.")
elif stock_predicho <= 150000:
    st.success("🟢 Escenario Óptimo: Las condiciones laborales logran retener y retornar el capital intelectual.")
else:
    st.warning("🟡 Escenario Inercial: El flujo de emigración cualificada se mantiene estable en la media histórica.")

# ==============================================================================
# 6. NOTA METODOLÓGICA DINÁMICA (AL PIE DE LA PÁGINA)
# ==============================================================================
st.markdown("---")

if tipo_modelo == "Modelo de Simulación Teórica (Signos Corregidos)":
    st.info(
        "💡 **Enfoque Teórico Activo:** Ideal para la presentación ejecutiva ante el tribunal el jueves 25 de junio. "
        "Permite simular de forma lógica el impacto de tus **Recomendaciones Estratégicas** del Capítulo 9 "
        "(Incentivos STEM y mitigación de la brecha)."
    )
else:
    st.warning(
        "⚠️ **Enfoque Estadístico Puro:** Muestra el comportamiento matemático estricto extraído de Eurostat. "
        "Sirve para demostrar al tribunal tu dominio técnico sobre las limitaciones muestrales y la **correlación espuria**."
    )