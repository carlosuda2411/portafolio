# Guía de Contribución — Chatbot EcoMarket

Gracias por contribuir al chatbot de EcoMarket. Esta guía describe cómo configurar el entorno, entender la arquitectura y proponer cambios de forma ordenada.

## Configuración inicial

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repo>
   cd chatbot_ecomarket
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Mac / Linux
   # venv\Scripts\activate    # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env       # Mac / Linux
   # copy .env.example .env   # Windows
   ```

   Editar `.env`:
   ```env
   OPENAI_API_KEY=sk-...
   LOCAL_NLP_ENABLED=true
   ```

   No commitear `.env` ni claves reales.

5. **Generar la base de datos**
   ```bash
   python scripts/regenerate_db.py
   ```

   Alternativa: ejecutar el notebook `notebooks/01_base_datos.ipynb` completo.

6. **Lanzar la app**
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Estructura del proyecto

```
chatbot_ecomarket/
├── app/
│   └── streamlit_app.py       # Interfaz de chat
├── data/
│   └── ecomarket.db           # SQLite (generada, no commitear)
├── notebooks/                 # Desarrollo por capas (Jupyter)
├── scripts/
│   └── regenerate_db.py       # Actualiza catálogo/promos desde notebook 01
├── src/                       # Código de producción
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
├── README.md
└── CONTRIBUTING.md
```

## Arquitectura y dónde tocar cada cosa

```
Usuario → Streamlit → EcoMarketRouter
                          ├─ NLP local → SQLite
                          └─ OpenAI + 11 tools → SQLite
```

| Archivo | Responsabilidad |
|---------|-----------------|
| `src/intent_router.py` | Clasificar intención del usuario (producto, promo, pedido, saludo…) |
| `src/local_responder.py` | Generar respuesta local cuando la intención es simple |
| `src/router.py` | Decidir NLP local vs OpenAI; registrar turnos en el historial |
| `src/queries.py` | Toda la lógica de BD: búsqueda, promos, pedidos, listas |
| `src/agent.py` | Prompt del LLM, definición de tools y ejecución |
| `app/streamlit_app.py` | UI, sidebar, recarga de BD, sesión de chat |
| `notebooks/01_base_datos.ipynb` | Catálogo, promos y datos de ejemplo |

### Cuándo modificar NLP local vs LLM

- **NLP local:** consultas directas y repetitivas (productos, categorías, frutas/verduras, promos, pedidos con email). Cambios en `intent_router.py` y `local_responder.py`.
- **OpenAI:** flujos multi-turno (crear pedido, confirmaciones, devoluciones, listas). Cambios en `agent.py` y, si hace falta, nuevas funciones en `queries.py` registradas como tools.

Si añades una tool nueva en `agent.py`, implementa la función en `queries.py` y regístrala en el diccionario de herramientas del agente.

## Base de datos

### Generación y recarga

- `python scripts/regenerate_db.py` ejecuta las celdas de `01_base_datos.ipynb`.
- Por defecto `RESET_DB = False`: **conserva pedidos**, detalle, devoluciones y tickets; actualiza catálogo y promociones.
- `RESET_DB = True` borra la BD y la regenera desde cero (50 pedidos de ejemplo).

### Convenciones al editar datos

- Los productos del catálogo se identifican por **nombre**, no por ID fijo.
- Las promociones se vinculan al producto por nombre (`_id_producto()` en el notebook).
- Al recargar, el **stock de productos existentes no se resetea** (respeta ventas reales).
- Las fechas de promociones son **relativas a hoy** para que sigan vigentes al regenerar.

### Explorar la BD manualmente

Usa `notebooks/05_consultas_db.ipynb` para inspeccionar tablas sin tocar la app.

## Orden de los notebooks

1. `01_base_datos.ipynb` — crea o actualiza `data/ecomarket.db`
2. `02_funciones_consulta.ipynb` — prueba funciones de consulta
3. `03_agente_llm.ipynb` — agente OpenAI con tools
4. `04_orquestacion.ipynb` — router híbrido
5. `05_consultas_db.ipynb` — exploración de tablas

El código que usa la app está en `src/` y `app/`. Los notebooks documentan el desarrollo; no dupliques lógica entre notebook y `src/` sin sincronizar.

## Flujo de trabajo con Git

1. **Actualizar main y crear rama**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/descripcion-corta
   ```

2. **Commits frecuentes y descriptivos**
   ```bash
   git add .
   git commit -m "feat: descripción breve del cambio"
   ```

3. **Subir y abrir Pull Request**
   ```bash
   git push -u origin feat/descripcion-corta
   ```

   En GitHub: Pull Request hacia `main`, con al menos un revisor del equipo.

### Convención de commits

| Prefijo | Uso |
|---------|-----|
| `feat:` | Nueva funcionalidad |
| `fix:` | Corrección de bug |
| `docs:` | Documentación |
| `refactor:` | Reestructuración sin cambio funcional |
| `test:` | Tests |

### Qué no commitear

- `.env` y claves API
- `data/ecomarket.db` (está en `.gitignore`)
- Outputs pesados de notebooks (limpiar celdas si no aportan)

## Tests

Ejecutar antes de abrir un PR:

```bash
python -m unittest tests.test_nlp_queries -v
```

Añade tests en `tests/test_nlp_queries.py` cuando cambies:

- Clasificación de intenciones (`intent_router.py`)
- Respuestas locales (`local_responder.py`)
- Consultas críticas de BD (`queries.py`): promos, pedidos, búsqueda

Si la BD no existe, algunos tests se omiten; genera la BD con `regenerate_db.py` primero.

## Ejecutar Streamlit

### Requisitos previos

- Entorno virtual activado
- `data/ecomarket.db` generada
- `.env` con `OPENAI_API_KEY` válida

### Comando básico

```bash
streamlit run app/streamlit_app.py
```

Abre `http://localhost:8501`.

### Opciones útiles

```bash
# Puerto distinto
streamlit run app/streamlit_app.py --server.port 8502

# Recarga al guardar archivos
streamlit run app/streamlit_app.py --server.runOnSave true

# Sin abrir navegador automáticamente
streamlit run app/streamlit_app.py --server.headless true
```

### Recargar catálogo desde la app

El sidebar incluye **Recargar BD y bot**: vuelve a leer productos y promociones sin borrar pedidos (equivalente a `regenerate_db.py` con `RESET_DB = False`).

### Hot-reload de código

Streamlit detecta cambios en `app/` y `src/`. Tras guardar, pulsa **Rerun** o activa `--server.runOnSave true`.

Para limpiar caché interna:

```bash
streamlit cache clear
```

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | Activar venv e instalar `pip install -r requirements.txt` |
| Error de API key | Revisar `OPENAI_API_KEY` en `.env` |
| `No se encontró data/ecomarket.db` | `python scripts/regenerate_db.py` |
| Promos desalineadas con productos | Regenerar BD; promos deben usar nombre de producto, no ID fijo |
| Pedidos desaparecen al recargar | Verificar `RESET_DB = False` en notebook 01 |
| Puerto en uso | `--server.port 8502` o cerrar proceso previo |
| NLP no responde localmente | `LOCAL_NLP_ENABLED=true` en `.env`; reiniciar Streamlit |
| Comportamiento raro tras cambios | `streamlit cache clear` y **Nueva conversación** en sidebar |

## Configuración avanzada de Streamlit (opcional)

Crear `.streamlit/config.toml`:

```toml
[server]
port = 8501
runOnSave = true

[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

---

Proyecto académico — Master Business Analytics (2025)
