# ¡Hola! Soy Carlos Valverde Gaya 👋📊
### Data Analyst | Especializado en Business Analytics

Bienvenido a mi portafolio de proyectos. Soy un profesional con formación híbrida en **Administración y Dirección de Empresas (ADE)** y un **Máster Universitario en Business Analytics**, lo que me permite actuar como *Data Translator*: entiendo las necesidades estratégicas del negocio y las resuelvo mediante el desarrollo técnico y el análisis avanzado de datos.

Tengo experiencia real en entornos empresariales aplicando **SQL, Python y Power BI** para la generación de informes directivos, automatización de procesos ETL y análisis financieros y sectoriales de mercado de alto impacto (modelos TAM/SAM/SOM).

---

## 📁 Proyectos Destacados

### 1. [Predicción de la Fuga de Cerebros en España (2014–2030) 🧠✈️](./tfm-portafolio)
* **Descripción:** Mi Trabajo Fin de Máster (TFM). Un ecosistema analítico integral desarrollado bajo la metodología **CRISP-DM** para modelar cuantitativamente el impacto de la brecha salarial y la sobrecualificación en el éxodo de talento cualificado en España.
* **Foco Técnico:** Regresión Lineal Múltiple ($R^2 = 0.978$), validación de supuestos clásicos de Gauss-Markov (Shapiro-Wilk y Breusch-Pagan) y simulación estocástica de **Monte Carlo con 10,000 iteraciones** (`SciPy`) para la evaluación de riesgos.
* **Despliegue de Negocio:** Diseño de un **Dashboard ejecutivo en Power BI** que integra análisis espacial (mapas coropléticos) y simulación dinámica de escenarios mediante **Parámetros What-If (lógica DAX avanzada)** para evaluar el impacto de políticas públicas de retención.

### 2. [Breathing Beijing: Análisis Dimensional y Simulaciones Ambientales 🇨🇳🌫️](./beijing-air-quality)
* **Descripción:** Un análisis unificado en espejo para diagnosticar las dinámicas de contaminación extrema de material particulado (PM2.5) en Beijing, dividiéndose en dos aproximaciones tecnológicas independientes empleando la misma información:
  * **Fase SQL (Ingeniería de Datos):** Diseño e implementación desde cero de un **Data Warehouse (Modelo en Estrella)** bajo el esquema `beijing_dw`. Creación automatizada de tablas de hechos y dimensiones, cargas masivas (`COPY`), optimización con índices y analítica temporal avanzada mediante **Funciones de Ventana (Window Functions)** y CTEs para medir medias móviles de Ozono ($O_3$) y el "efecto lavado" de la lluvia mediante `LAG` y `LEAD`.
  * **Fase Python (Machine Learning Supervisado):** Análisis Exploratorio de Datos (EDA) estacional e implementación de flujos de trabajo automatizados mediante **`Pipelines` y `ColumnTransformer` de Scikit-Learn** (con `SimpleImputer` y `LinearRegression`). El modelo alcanzó un $R^2 = 0.669$ y sirvió como motor contrafactual para simular planes de restricción de tráfico en hora punta, demostrando que una reducción del 10% del tráfico mitiga un 12.19% el PM2.5.

### 3. [Chatbot EcoMarket: Asistente Conversacional Híbrido con IA 🛒🤖](./chatbot-ecomarket)
* **Descripción:** Diseño y despliegue de un asistente virtual interactivo *end-to-end* en **Streamlit** diseñado para optimizar los flujos de atención al cliente y la gestión operativa de un supermercado electrónico.
* **Foco Técnico:** Implementación de una **arquitectura híbrida de enrutamiento** (`EcoMarketRouter`) para optimizar costes de cómputo. Un clasificador local con **NLP y pruebas unitarias (`unittest`)** absorbe consultas rutinarias (catálogo, promociones) sin consumir tokens externos. Consultas ambiguas o transaccionales son delegadas al modelo **OpenAI GPT-4o-mini**, el cual cuenta con **11 herramientas mapeadas (*Function Calling*)** para interactuar en tiempo real con una base de datos relacional `SQLite`.
* **Impacto Operativo:** El bot gestiona de forma autónoma flujos complejos de creación de pedidos (calculando subtotales, costes de envío y aplicando promociones vigentes), consultas postventa (estados de envío, tickets de soporte) y generación inteligente de listas de compra temáticas adaptadas al presupuesto del cliente.

---

## 🛠️ Tecnologías y Competencias Técnicas

* **Business Intelligence & Visualización:** Power BI (Nivel Profesional), Tableau (Básico), Excel Avanzado.
* **Lenguajes y Ciencia de Datos:** Python (ETL, EDA, ML Pipelines, Scikit-Learn, Statsmodels, SciPy) y SQL Avanzado (PostgreSQL, SQLite, Window Functions, Dimensional Modeling).
* **Procesos y Estrategia:** Metodología CRISP-DM, análisis sectorial y financiero (TAM/SAM/SOM), traducción de requerimientos técnicos a negocio (*Data Translator*).

---

## 🎓 Formación y Certificaciones Clave

* **Máster Universitario en Business Analytics** | +Universidad Europea de Andalucía (2025 - 2026).
* **Grado en Administración y Dirección de Empresas (ADE)** | Universidad de Almería (2019 - 2025)+.
* **Certificaciones Destacadas:** * *Cisco Networking Academy:* Fundamentos de Python 1 y 2.
  * *Especializaciones Udemy:* Power BI (Análisis Profesional), SQL desde Cero, Tableau de la A a la Z y Excel Total.

---

## ✉️ ¡Conectemos!

Estoy buscando oportunidades para incorporarme como **Data Analyst / Business Analyst**, aportando rigor analítico, visión de negocio y pensamiento estructurado a equipos orientados a objetivos.

* **📍 Ubicación:** Málaga, España (Disponibilidad geográfica y vehículo propio) 
* **💼 LinkedIn:** [linkedin.com/in/carlos-valverde-gaya](https://linkedin.com/in/carlos-valverde-gaya) 
* **📧 Email:** carlosvalverdegaya@gmail.com 
* **📞 Teléfono:** +34 647 072 373 
