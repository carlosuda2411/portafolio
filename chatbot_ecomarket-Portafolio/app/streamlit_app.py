"""
Interfaz Streamlit para el chatbot EcoMarket.
Ejecutar con: streamlit run app/streamlit_app.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import importlib
from src.router import EcoMarketRouter
from src.database import obtener_info_bd
from src import agent, queries, database, intent_router, local_responder, router

MENSAJE_BIENVENIDA = (
    "¡Hola! 👋 Soy **EcoBot**, tu asistente de EcoMarket.\n\n"
    "Puedo ayudarte con:\n"
    "- 🔍 Buscar productos y ver disponibilidad\n"
    "- 🛒 Hacer un pedido nuevo (pago contra entrega)\n"
    "- 📦 Consultar el estado de tus pedidos\n"
    "- 🏷️ Ver promociones vigentes\n"
    "- 🔄 Gestionar devoluciones\n\n"
    "¿En qué puedo ayudarte hoy?"
)


def reiniciar_chat():
    st.session_state.mensajes = [{
        "role": "assistant",
        "content": MENSAJE_BIENVENIDA,
    }]


def recargar_aplicacion():
    importlib.reload(database)
    importlib.reload(queries)
    importlib.reload(intent_router)
    importlib.reload(local_responder)
    importlib.reload(agent)
    importlib.reload(router)
    st.session_state.bot = router.EcoMarketRouter()
    reiniciar_chat()


st.set_page_config(
    page_title="EcoMarket - Asistente Virtual",
    page_icon="🛒",
    layout="centered",
)

st.markdown("""
<style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .bot-header { text-align: center; padding: 1rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bot-header">
    <h1>🛒 EcoMarket</h1>
    <p>Asistente Virtual - Pregúntame sobre productos, pedidos, promociones o devoluciones</p>
</div>
""", unsafe_allow_html=True)

if 'bot' not in st.session_state:
    st.session_state.bot = EcoMarketRouter()

if 'mensajes' not in st.session_state:
    st.session_state.mensajes = []
    reiniciar_chat()

with st.sidebar:
    st.markdown("### ⚙️ Opciones")

    info_bd = obtener_info_bd()
    if info_bd.get('existe'):
        st.caption(
            f"BD: {info_bd['productos']} productos · "
            f"{info_bd['pedidos']} pedidos · "
            f"actualizada {info_bd['modificado']}"
        )
    else:
        st.warning("No se encontró data/ecomarket.db. Ejecuta `python scripts/regenerate_db.py`.")

    if st.button("🔄 Recargar BD y bot", use_container_width=True):
        st.session_state.bot.recargar_catalogo()
        recargar_aplicacion()
        st.rerun()

    if st.button("🗑️ Nueva conversación", use_container_width=True):
        st.session_state.bot.resetear_conversacion()
        reiniciar_chat()
        st.rerun()

    st.markdown("---")
    st.caption(
        "NLP local activo para consultas simples. "
        "Desactiva con LOCAL_NLP_ENABLED=false en .env"
    )

    st.markdown("---")
    st.markdown("### 💡 Ejemplos (NLP local, sin tokens)")
    st.markdown("""
    - "¿Tienen leche?"
    - "¿Qué frutas hay?"
    - "¿Qué promociones hay?"
    - "Pedidos de maria.garcia@email.com"
    """)
    st.markdown("### 🛒 Hacer pedido (OpenAI)")
    st.markdown("""
    - "Quiero comprar 2 leches enteras"
    - Dirección con **Madrid**, **Málaga** o **Valencia**
    - Confirma cuando el bot muestre el resumen
    """)

    st.markdown("---")
    st.markdown(
        "<small>⚡ Simples → NLP local · 🤖 Complejas → OpenAI GPT-4o-mini</small>",
        unsafe_allow_html=True,
    )

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando..."):
                respuesta = st.session_state.bot.responder(prompt)
            st.markdown(respuesta)
            fuente = st.session_state.bot.ultima_fuente
            if fuente == 'local':
                st.caption("⚡ Respuesta local (sin OpenAI)")
            else:
                st.caption("🤖 Respuesta con OpenAI")
            st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
        except RuntimeError as e:
            error_msg = f"❌ {e}"
            st.error(error_msg)
            st.session_state.mensajes.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"❌ Error inesperado: {e}"
            st.error(error_msg)
            st.session_state.mensajes.append({"role": "assistant", "content": error_msg})
