# 🛒 Chatbot EcoMarket

Asistente virtual para el supermercado **EcoMarket**. Responde consultas sobre catálogo, promociones y pedidos, y guía al cliente en flujos conversacionales más complejos (nuevos pedidos, devoluciones, listas de compra).

- ✅ Consultar productos y categorías
- 📦 Consultar pedidos (por email)
- 🏷️ Promociones vigentes
- 🔄 Devoluciones y tickets de soporte
- 🛒 Crear pedidos (Madrid, Málaga, Valencia — pago contra entrega)
- 📋 Listas de compra temáticas (saludable, vegano, desayuno…)

## Funcionalidades

| Área | Qué puede hacer |
|------|-----------------|
| **Catálogo** | Buscar productos por nombre (coincidencia flexible), listar categorías, filtrar frutas o verduras |
| **Promociones** | Ver ofertas vigentes (top 5 o listado completo), filtrar por categoría, producto o día (ej. martes) |
| **Pedidos** | Consultar historial por email, ver detalle, calcular total con promos + domicilio (2 €), crear pedido nuevo |
| **Postventa** | Registrar y consultar devoluciones, abrir tickets de soporte |
| **Listas de compra** | Generar listas temáticas (saludable, vegano, proteico, económico, desayuno…) con presupuesto opcional |

**Cobertura de envío:** Madrid, Málaga y Valencia (pago contra entrega).

## Tecnologías

- **Python 3.10+**
- **OpenAI GPT-4o-mini** — LLM con function calling (11 herramientas)
- **NLP local** — consultas simples sin consumir tokens de OpenAI
- **SQLite** — catálogo, pedidos, promociones, devoluciones y tickets
- **Streamlit** — interfaz de chat
- **Jupyter** — notebooks de desarrollo por capas

## Instalación

```bash
git clone <url-del-repo>
cd chatbot_ecomarket

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env         # Mac / Linux
```

Edita `.env` con tu API key de OpenAI:

```env
OPENAI_API_KEY=sk-...
LOCAL_NLP_ENABLED=true
```

Genera o actualiza la base de datos:

```bash
python scripts/regenerate_db.py
```

Lanza la interfaz:

```bash
streamlit run app/streamlit_app.py
```

La app abre en `http://localhost:8501`.

## Base de datos

El script `scripts/regenerate_db.py` ejecuta la lógica de `notebooks/01_base_datos.ipynb`.

| Tabla | Contenido |
|-------|-----------|
| `productos` | ~72 productos en 13 categorías |
| `pedidos` / `detalle_pedido` | Historial de pedidos |
| `promociones` | 13 ofertas con fechas relativas a hoy |
| `devoluciones` | Solicitudes de ejemplo |
| `tickets_soporte` | Casos de soporte de ejemplo |

**Recarga sin perder pedidos:** en el notebook, la variable `RESET_DB = False` (por defecto) conserva pedidos, detalle, devoluciones y tickets al recargar. Solo actualiza catálogo y promociones. Los productos se vinculan por **nombre** (no por ID fijo), y el stock no se resetea para respetar ventas reales.

Para empezar de cero: `RESET_DB = True` en la celda de conexión del notebook.

Desde Streamlit, el botón **Recargar BD y bot** del sidebar vuelve a leer el catálogo sin reiniciar la conversación completa.

## Arquitectura híbrida

```
Usuario → Streamlit → EcoMarketRouter
                          ├─ NLP local (intent_router + local_responder) → SQLite
                          └─ OpenAI GPT-4o-mini + 11 tools → SQLite
```

### NLP local (⚡ sin tokens)

Saludos, ayuda, búsqueda de productos, categorías, frutas/verduras, promociones y consulta de pedidos cuando el email está en el mensaje.

Activar/desactivar con `LOCAL_NLP_ENABLED` en `.env`.

### OpenAI (🤖 con tools)

Pedidos conversacionales, confirmaciones, devoluciones, tickets, listas de compra y consultas ambiguas.

Herramientas disponibles: `buscar_producto`, `buscar_por_categoria`, `consultar_pedidos`, `obtener_detalle_pedido`, `calcular_total_pedido`, `crear_pedido`, `obtener_promociones`, `registrar_devolucion`, `consultar_devoluciones`, `crear_ticket_soporte`, `generar_lista_compra`.

## Ejemplos de uso

**NLP local:**
- *¿Tienen leche?*
- *¿Qué frutas hay?*
- *¿Qué promociones hay?*
- *Pedidos de maria.garcia@email.com*

**OpenAI:**
- *Quiero comprar 2 leches enteras y un pan integral*
- *Necesito devolver el pedido 12*
- *Hazme una lista saludable con 30 euros*

## Tests

```bash
python -m unittest tests.test_nlp_queries -v
```

## Estructura del proyecto

```
chatbot_ecomarket/
├── app/
│   └── streamlit_app.py       # Interfaz de chat
├── data/
│   └── ecomarket.db           # SQLite (generada, no commitear)
├── notebooks/
│   ├── 01_base_datos.ipynb    # Creación y recarga de la BD
│   ├── 02_funciones_consulta.ipynb
│   ├── 03_agente_llm.ipynb
│   ├── 04_orquestacion.ipynb
│   └── 05_consultas_db.ipynb  # Exploración manual de tablas
├── scripts/
│   └── regenerate_db.py       # Actualiza catálogo/promos desde notebook 01
├── src/
│   ├── agent.py               # OpenAI + function calling
│   ├── intent_router.py       # Clasificador NLP local
│   ├── local_responder.py     # Respuestas sin LLM
│   ├── router.py              # Orquestador híbrido
│   ├── queries.py             # Consultas BD, pedidos, promos, listas
│   └── database.py            # Conexión SQLite
├── tests/
│   └── test_nlp_queries.py
├── .env.example
├── requirements.txt
├── CONTRIBUTING.md            # Guía para el equipo
└── README.md
```

## Notebooks (orden recomendado)

1. `01_base_datos.ipynb` — genera `data/ecomarket.db`
2. `02_funciones_consulta.ipynb` — prueba consultas sobre la BD
3. `03_agente_llm.ipynb` — agente OpenAI con tools
4. `04_orquestacion.ipynb` — router híbrido
5. `05_consultas_db.ipynb` — inspección de tablas

El código de producción vive en `src/` y `app/`; los notebooks documentan el desarrollo por capas.

---

Proyecto académico — Master Business Analytics UEA 2025-2026

- Laura Fernández Gallardo
- Esteban Orozco García
- Ignacio Ros Jiménez
- Manuel Rubio Sánchez
- Danna Alejandra Sarmiento Martínez
- Carlos Valverde Gaya
