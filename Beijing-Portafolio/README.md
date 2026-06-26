# Breathing Beijing: Diagnóstico en SQL y Simulación Predictiva en Python (2013–2017) 🇨🇳🌫️
### Proyecto de Fundamentos en Data Science | Equipo Rojo

Este repositorio contiene el análisis integral de la calidad del aire en Beijing (2013-2017) enfocado en las partículas peligrosas PM2.5 y PM10[cite: 4, 6]. El proyecto se ejecutó en **dos fases totalmente independientes empleando la misma información**: primero, un desarrollo enfocado en Ingeniería de Datos y explotación de bases de datos relacionales con **SQL**, y segundo, un enfoque de Data Science, análisis estadístico y simulación contrafactual con **Python**[cite: 3, 4, 6].

---

## 🚀 Fase 1: Arquitectura de Datos y Analítica Temporal (PostgreSQL)

El objetivo de esta primera etapa fue diseñar un entorno performante y estructurado desde cero para centralizar y explotar los millones de registros dispersos de 12 estaciones de monitoreo de la ciudad[cite: 3, 5].

* **Modelado Dimensional (Modelo en Estrella):** Implementación del esquema `beijing_dw` estructurado en una tabla de hechos central (`fact_datos`), una tabla de staging para la ingesta (`staging_datos`) y dos dimensiones optimizadas (`dim_station` y `dim_time`) con claves primarias y foráneas bien definidas[cite: 3].
* **Automatización ETL:** Creación de scripts SQL estructurados para la carga masiva de datos mediante comandos `COPY`[cite: 3].
* **Optimización y Rendimiento:** Creación de índices B-Tree (`idx_fact_station`, `idx_fact_time`, `idx_time_ts`) para agilizar las consultas analíticas sobre la tabla de hechos[cite: 3].
* **Analítica Avanzada con Window Functions y CTEs:**
  * Uso de expresiones comunes de tabla (`WITH`) y **Funciones de Ventana** (`AVG() OVER ... ROWS BETWEEN 7 PRECEDING AND CURRENT ROW`) para calcular la media móvil de 8 horas del Ozono ($O_3$) y extraer sus picos máximos diarios[cite: 3].
  * Implementación de funciones de desplazamiento temporal (`LAG` y `LEAD`) para capturar el contexto de las precipitaciones y medir la variación del PM10 antes, durante y hasta 7 días después de un evento de lluvia, evaluando la persistencia del efecto lavado atmosférico[cite: 3, 4].

---

## 🐍 Fase 2: Analítica Avanzada, Machine Learning y Simulación (Python)

En esta segunda etapa independiente, se utilizó el mismo conjunto de datos para aplicar técnicas de modelado predictivo mediante Machine Learning, entender las correlaciones climáticas y predecir el impacto de políticas de movilidad urbana[cite: 4, 6].

* **Preprocesamiento Científico:** Tratamiento e imputación de registros nulos mediante ordenamiento lógico por estación y aplicación de **interpolación lineal** y *backward fill* (`bfill`) para asegurar la continuidad de las series temporales.
* **Análisis de Correlación y Estacionalidad:** Descubrimiento mediante mapas de calor (`seaborn`) de una estacionalidad de la contaminación en invierno (noviembre a febrero) impulsada por el uso de calefacción por carbón, y validación del estancamiento de partículas finas cuando la velocidad del viento baja de $0.9 \text{ m/s}$[cite: 4, 6].
* **Modelado Predictivo (Machine Learning Pipelines):** Construcción de un flujo de trabajo automatizado mediante un **`Pipeline`** y `ColumnTransformer` de `scikit-learn`. Implementamos un `SimpleImputer` por mediana para robustecer el set de datos y entrenamos un algoritmo de **Regresión Lineal** (`LinearRegression`) para predecir el PM2.5, evaluando su rendimiento con un **MAE de 32.35** y un **$R^2$ de 0.669**[cite: 6].
* **Simulación de Escenarios Contrafactuales de Tráfico:** Utilizando el Pipeline entrenado como motor predictivo, se simuló el impacto de restringir el tráfico en horas punta (empleando el $NO_2$ y el $CO$ como *proxies* de emisiones vehiculares)[cite: 6]:
  * **Reducción del 10% del tráfico:** Genera una caída estimada del 12.19% en PM2.5 ($-9.54\text{ }\mu\text{g/m}^3$)[cite: 6].
  * **Restricciones del 20% y 30%:** Mitigan el contaminante en un **26.11%** y un **39.16%** respectivamente en hora punta[cite: 6].
  * **Optimización Horaria:** Se identificó que la intervención en la franja de 18:00 a 20:00 h genera el mayor rendimiento porcentual relativo con un **14.36%** de caída de la contaminación por partículas finas[cite: 6].

---

## 🛠️ Stack Tecnológico Utilizado

* **Entorno SQL:** PostgreSQL (Diseño de Data Warehouse, DDL, DML avanzado, Window Functions y CTEs)[cite: 3].
* **Entorno Python:** Python 3.x, `pandas`, `NumPy`, `statsmodels`, `scikit-learn` (`Pipeline`, `ColumnTransformer`), `matplotlib` y `seaborn`[cite: 6].

---

## 📂 Contenido del Repositorio

* `📁 SQL-Engineering/` - Contiene los scripts `.sql` con la creación completa de la arquitectura del Data Warehouse, restricciones, índices y las consultas analíticas de negocio[cite: 3].
* `📁 Python-Analytics/` - Contiene el Jupyter Notebook (`Analisis_Aire.ipynb`) y el reporte interactivo (`Beijing_clean.html`) con la limpieza por interpolación lineal, el EDA meteorológico y el desarrollo de las simulaciones de tráfico[cite: 5, 6].
* `📄 Project beijin - RedTeam.pptx` - Presentación ejecutiva del proyecto con las conclusiones y propuestas estratégicas *data-driven* (App Air Pulse, urbanismo verde e incentivos industriales)[cite: 4].