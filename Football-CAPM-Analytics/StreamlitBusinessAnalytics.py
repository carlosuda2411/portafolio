import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.stats.api as sms
from statsmodels.stats.stattools import jarque_bera
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Configuración de página
st.set_page_config(page_title="Football CAPM Analytics", layout="wide", page_icon="⚽")

# ── Encabezado
st.title("⚽ CAPM Football Analytics Dashboard")
st.markdown("""
### Herramienta de Soporte Decisional para la Estimación del Coste de Capital ($K_e$)
*Trabajo Final — Business Analytics e Inteligencia Empresarial*

Este cuadro de mando evalúa el riesgo sistemático y el coste de capital de clubes de fútbol europeos
desde la perspectiva de un **inversor residente en España**, con homogeneización previa de divisas
a EUR y correcciones econométricas robustas (HAC Newey-West).
""")

# ══════════════════════════════════════════════════════════════════════
# UNIVERSO DE CLUBES
# ══════════════════════════════════════════════════════════════════════
club_config = {
    'Manchester United (MANU)':    ('MANU',     'EURUSD=X'),
    'Juventus (JUVE.MI)':          ('JUVE.MI',  'EUR'),
    'Borussia Dortmund (BVB.DE)':  ('BVB.DE',   'EUR'),
    'Lazio (SSL.MI)':              ('SSL.MI',   'EUR'),
    'Ajax (AJAX.AS)':              ('AJAX.AS',  'EUR'),
    'Porto (FCP.LS)':              ('FCP.LS',   'EUR'),
    'Galatasaray (GSRAY.IS)':      ('GSRAY.IS', 'EURTRY=X'),
    'Fenerbahçe (FENER.IS)':       ('FENER.IS', 'EURTRY=X'),
    'Beşiktaş (BJKAS.IS)':         ('BJKAS.IS', 'EURTRY=X'),
    'Trabzonspor (TSPOR.IS)':      ('TSPOR.IS', 'EURTRY=X'),
    'Celtic (CCP.L)':              ('CCP.L',    'EURGBP=X'),
}

market_benchmark = '^STOXX50E'

# ══════════════════════════════════════════════════════════════════════
# BARRA LATERAL
# ══════════════════════════════════════════════════════════════════════
st.sidebar.header("⚙️ Parámetros de Simulación")

club_nombre = st.sidebar.selectbox(
    "Club bajo análisis:",
    list(club_config.keys())
)
ticker_club, fx_ticker = club_config[club_nombre]

st.sidebar.write(f"🔍 DEBUG: club_nombre={club_nombre} | ticker_club={ticker_club}")

rf_anual  = st.sidebar.slider("Tasa Libre de Riesgo anual (Rf)", 0.00, 0.08, 0.033, 0.001, format="%.3f")
mrp       = st.sidebar.slider("Prima de Riesgo de Mercado (MRP)", 0.02, 0.10, 0.047, 0.001, format="%.3f")
rm_anual  = rf_anual + mrp
window    = st.sidebar.slider("Ventana Beta Rodante (días)", 30, 120, 60, 5)

st.sidebar.markdown(f"""
---
**Parámetros actuales:**
- $R_f$ = {rf_anual*100:.1f}%
- MRP = {mrp*100:.1f}%
- $E(R_m)$ = {rm_anual*100:.1f}%
- Benchmark: Euro Stoxx 50
""")

# ══════════════════════════════════════════════════════════════════════
# CARGA DE DATOS (con caché)
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_data():
    """Descarga datos de Yahoo Finance y homogeneiza a EUR."""
    end   = datetime.today()
    start = end - timedelta(days=3 * 365)

    tickers_all = list(set(
        [c[0] for c in club_config.values()] +
        [market_benchmark] +
        [c[1] for c in club_config.values() if c[1] != 'EUR']
    ))

    raw_all = yf.download(tickers_all, start=start, end=end, progress=False)

    level0 = raw_all.columns.get_level_values(0).unique()
    if 'Adj Close' in level0:
        raw = raw_all['Adj Close']
    elif 'adj_close' in level0:
        raw = raw_all['adj_close']
    else:
        raw = raw_all['Close']

    precios_eur = pd.DataFrame(index=raw.index)
    precios_eur[market_benchmark] = raw[market_benchmark]

    for nombre, (ticker, fx) in club_config.items():
        if ticker not in raw.columns:
            continue
        if fx == 'EUR':
            precios_eur[ticker] = raw[ticker]
        else:
            if fx not in raw.columns:
                continue
            price = raw[ticker]
            # Celtic (CCP.L): LSE cotiza en GBp (peniques) → dividir por 100 antes de convertir
            if ticker == 'CCP.L':
                price = price / 100
            precios_eur[ticker] = price / raw[fx]

    precios_eur = precios_eur.dropna(how='all').ffill().dropna()
    rentabilidades = precios_eur.pct_change().dropna()
    return rentabilidades, start, end


with st.spinner("Conectando con Yahoo Finance y homogeneizando divisas a EUR…"):
    try:
        rentabilidades, start_date, end_date = load_data()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

# ══════════════════════════════════════════════════════════════════════
# COMPROBACIÓN DE DISPONIBILIDAD
# ══════════════════════════════════════════════════════════════════════
if ticker_club not in rentabilidades.columns or market_benchmark not in rentabilidades.columns:
    st.error(
        f"❌ No hay datos suficientes para **{club_nombre}** o el benchmark. "
        "Comprueba tu conexión o selecciona otro club."
    )
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# CÁLCULO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════
rf_diario = (1 + rf_anual)**(1/252) - 1

Y = rentabilidades[ticker_club] - rf_diario
X = sm.add_constant(rentabilidades[market_benchmark] - rf_diario)

# OLS estándar (para diagnóstico)
modelo_ols = sm.OLS(Y, X).fit()

# Tests de supuestos
bp_stat, bp_p, _, _ = sms.het_breuschpagan(modelo_ols.resid, modelo_ols.model.exog)
dw_stat              = sm.stats.durbin_watson(modelo_ols.resid)
jb_stat, jb_p, _, _ = jarque_bera(modelo_ols.resid)

# Modelo con HAC Newey-West (siempre, por conservadurismo)
modelo = sm.OLS(Y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 4})

beta  = modelo.params[market_benchmark]
alfa  = modelo.params['const']
r2    = modelo.rsquared
p_val = modelo.pvalues[market_benchmark]
ke    = rf_anual + beta * mrp

# ══════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Beta (β)", f"{beta:.3f}")
c2.metric("Coste de Capital Ke", f"{ke*100:.2f}%")
c3.metric("Alpha de Jensen (diario)", f"{alfa:.5f}")
c4.metric("R² del modelo", f"{r2:.3f}")
c5.metric("Prima de Riesgo (MRP)", f"{mrp*100:.1f}%")

# ══════════════════════════════════════════════════════════════════════
# INTERPRETACIÓN AUTOMÁTICA
# ══════════════════════════════════════════════════════════════════════
sig = "***" if p_val < 0.01 else ("**" if p_val < 0.05 else ("*" if p_val < 0.10 else "n.s."))

if beta < 0.0:
    tipo = "**activo inversamente correlado** con el mercado"
    color_msg = "info"
elif beta < 0.5:
    tipo = "**activo fuertemente defensivo** (baja correlación estructural con el ciclo económico)"
    color_msg = "info"
elif beta < 1.0:
    tipo = "**activo defensivo moderado**"
    color_msg = "info"
else:
    tipo = "**activo con alta co-movilidad** respecto al mercado"
    color_msg = "warning"

msg = (
    rf"**{club_nombre}** se comporta como {tipo}. "
    rf"$\beta$ = {beta:.3f} (p-valor: {p_val:.4f} {sig}). "
    rf"El R² = {r2:.3f} confirma que el riesgo idiosincrático domina la varianza del activo — "
    "resultado coherente con la anomalía sectorial documentada en la literatura (Robeco, 2023)."
)

if color_msg == "info":
    st.info(msg)
else:
    st.warning(msg)

# ══════════════════════════════════════════════════════════════════════
# DIAGNÓSTICO ECONOMÉTRICO
# ══════════════════════════════════════════════════════════════════════
with st.expander("🔬 Diagnóstico de Supuestos de Gauss-Markov (OLS estándar)"):
    d1, d2, d3 = st.columns(3)
    d1.metric(
        "Breusch-Pagan (Homocedasticidad)",
        f"p = {bp_p:.4f}",
        delta="❌ Heterocedástico" if bp_p < 0.05 else "✅ OK",
        delta_color="off"
    )
    d2.metric(
        "Durbin-Watson (No autocorrelación)",
        f"d = {dw_stat:.4f}",
        delta="❌ Autocorrelación" if (dw_stat < 1.5 or dw_stat > 2.5) else "✅ OK",
        delta_color="off"
    )
    d3.metric(
        "Jarque-Bera (Normalidad residuos)",
        f"p = {jb_p:.4f}",
        delta="❌ No normal (colas gordas)" if jb_p < 0.05 else "✅ OK",
        delta_color="off"
    )
    st.caption(
        "Se aplican errores estándar **HAC Newey-West (maxlags=4)** de forma universal "
        "para todos los clubes, garantizando robustez ante heterocedasticidad y autocorrelación "
        "típicas de retornos financieros diarios."
    )

# ══════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
g1, g2 = st.columns(2)

with g1:
    st.markdown("##### Recta de Regresión CAPM")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.scatter(
        rentabilidades[market_benchmark],
        rentabilidades[ticker_club],
        alpha=0.25, color='steelblue', s=12, label="Obs. diarias"
    )
    x_rng = np.linspace(rentabilidades[market_benchmark].min(),
                        rentabilidades[market_benchmark].max(), 100)
    ax1.plot(x_rng, alfa + beta * x_rng, color='crimson', linewidth=2,
             label=rf"$\beta$={beta:.3f}, $\alpha$={alfa:.5f}")
    ax1.axhline(0, color='grey', linestyle=':', linewidth=0.7)
    ax1.axvline(0, color='grey', linestyle=':', linewidth=0.7)
    ax1.set_xlabel("Exceso de retorno — Euro Stoxx 50", fontsize=9)
    ax1.set_ylabel(f"Exceso de retorno — {club_nombre.split('(')[0].strip()}", fontsize=9)
    ax1.legend(fontsize=8)
    ax1.set_title(rf"Modelo de mercado (R²={r2:.3f})", fontsize=10)
    plt.tight_layout()
    st.pyplot(fig1)

with g2:
    st.markdown("##### Inestabilidad Estructural — Beta Rodante")
    betas_r, fechas = [], []
    for i in range(window, len(rentabilidades)):
        v   = rentabilidades.iloc[i-window:i]
        Y_w = v[ticker_club] - rf_diario
        X_w = sm.add_constant(v[market_benchmark] - rf_diario)
        betas_r.append(sm.OLS(Y_w, X_w).fit().params[market_benchmark])
        fechas.append(rentabilidades.index[i])

    df_br = pd.Series(betas_r, index=fechas)

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(df_br, color='#003087', linewidth=1.3,
             label=rf"$\beta$ rodante {window}d")
    ax2.axhline(beta, color='crimson', linestyle='--', linewidth=1.5,
                label=rf"$\beta$ estática = {beta:.3f}")
    ax2.axhline(0, color='grey',   linestyle=':', linewidth=0.7)
    ax2.axhline(1, color='orange', linestyle=':', linewidth=0.7, label=r"$\beta$=1")
    ax2.fill_between(df_br.index, df_br, beta, alpha=0.08, color='#003087')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.set_ylabel(r"Coeficiente $\beta$", fontsize=9)
    ax2.set_xlabel("Fecha", fontsize=9)
    ax2.legend(fontsize=8)
    ax2.set_title(rf"$\beta$ dinámica — rango [{df_br.min():.2f}, {df_br.max():.2f}]", fontsize=10)
    plt.tight_layout()
    st.pyplot(fig2)

# ══════════════════════════════════════════════════════════════════════
# TABLA COMPARATIVA — TODOS LOS CLUBES
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📊 Comparativa Cross-Sectional — Universo Completo")

clubs_ok = [c[0] for c in club_config.values() if c[0] in rentabilidades.columns]
nombre_map = {c[0]: n for n, c in club_config.items()}

filas = []
for t in clubs_ok:
    Y_c = rentabilidades[t] - rf_diario
    X_c = sm.add_constant(rentabilidades[market_benchmark] - rf_diario)
    res = sm.OLS(Y_c, X_c).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
    b   = res.params[market_benchmark]
    ke_ = rf_anual + b * mrp
    ret = (1 + rentabilidades[t].mean())**252 - 1
    p_  = res.pvalues[market_benchmark]
    sig_= "***" if p_ < 0.01 else ("**" if p_ < 0.05 else ("*" if p_ < 0.10 else "n.s."))
    filas.append({
        "Club":              nombre_map.get(t, t),
        "Beta (β)":          round(b, 3),
        "Ke CAPM (%)":       round(ke_ * 100, 2),
        "Ret. Realizado (%)":round(ret * 100, 2),
        "R²":                round(res.rsquared, 3),
        "Sign. β":           sig_
    })

df_tabla = pd.DataFrame(filas).set_index("Club")
st.dataframe(df_tabla.style.highlight_max(subset=["Beta (β)", "Ke CAPM (%)"], color="#ffe0e0")
                            .highlight_min(subset=["Beta (β)", "Ke CAPM (%)"], color="#e0f0ff"),
             use_container_width=True)

st.caption(
    f"Rf = {rf_anual*100:.1f}% | MRP = {mrp*100:.1f}% | E(Rm) = {rm_anual*100:.1f}% | "
    f"Benchmark: Euro Stoxx 50 | Ventana: {start_date.strftime('%Y-%m-%d')} – {end_date.strftime('%Y-%m-%d')} | "
    "Errores HAC Newey-West (maxlags=4)"
)

# ══════════════════════════════════════════════════════════════════════
# PIE DE PÁGINA
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption(
    "**Nota metodológica:** todos los precios se convierten a EUR antes del cálculo de retornos. "
    "Celtic (CCP.L) cotiza en peniques GBp en el LSE; se aplica corrección ÷100 antes de la conversión. "
    "Fuentes: Yahoo Finance (yfinance) | statsmodels | Damodaran (2024) para MRP."
)