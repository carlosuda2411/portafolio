# Predicción de la Fuga de Cerebros en España (2014–2030) 🧠✈️
### Análisis Predictivo e Impacto de la Brecha Salarial y la Sobrecualificación

Este repositorio contiene el desarrollo técnico de mi **Trabajo Fin de Máster (TFM)** para el Máster Universitario en Analítica de Negocios (Business Analytics) en la Universidad Europea Andalucía. 

El proyecto aborda de manera cuantitativa el éxodo de talento cualificado en España, analizando el histórico (2014-2023) donde se registró un incremento del **56.9%** de egresados residiendo en la UE, y proyectando escenarios macroeconómicos hasta el año **2030**.

---

## 🚀 Estructura del Ecosistema Analítico (CRISP-DM)

El proyecto se ha desarrollado siguiendo el ciclo metodológico **CRISP-DM**, dividiéndose en las siguientes capas técnicas:

### 1. Modelado Predictivo (Python)
* **Regresión Lineal Múltiple (MCO):** Implementada para identificar las variables de empuje (*push*). El modelo final obtuvo un **$R^2$ de 0.978**, situando a la **brecha salarial por hora** como el predictor individual más robusto ($\beta = -22,449$; $p = 0.007$).
* **Validación Estadística:** Se verificó el cumplimiento de los supuestos clásicos de Gauss-Markov mediante los tests de Shapiro-Wilk (normalidad, $p = 0.718$) y Breusch-Pagan (homocedasticidad, $p = 0.274$).
* **Simulación de Monte Carlo:** Con el fin de añadir una métrica de riesgo a las proyecciones 2024-2030, se parametrizó una simulación estocástica de **10,000 iteraciones** utilizando la librería `SciPy`.

### 2. Segmentación de Destinos (Clustering K-means++)
Mediante analítica de corte transversal, se segmentaron los 8 países de destino principales en dos perfiles optimizados mediante el coeficiente de silueta ($k=2$):
* **Clúster 1 (Proximidad):** Destinos como Italia o Portugal, donde la cercanía cultural y geográfica mitiga el coste de instalación.
* **Clúster 2 (Oportunidad Económica):** Liderado por Alemania, Francia y Reino Unido, caracterizados por una alta atracción salarial y niveles de inversión en I+D que duplican la media española.

### 3. Despliegue e Interfaz Interactiva (Power BI)
Todo el motor analítico de Python se integró en un cuadro de mandos ejecutivo que incluye:
* Capa de análisis espacial mediante mapas coropléticos de concentración de talento.
* **Panel de Simulación Dinámica (Parámetros What-If):** Implementación de lógica DAX avanzada para que el usuario pueda modificar interactivamente tasas de desempleo juvenil o inversión en I+D, visualizando al instante el comportamiento de las curvas predictivas hacia 2030 (Escenarios Optimista, Tendencial y Pesimista).

---

## 🛠️ Tecnologías y Librerías Utilizadas

* **Lenguaje:** Python 3.x
* **Manipulación de Datos:** `pandas`, `NumPy`
* **Estadística y Machine Learning:** `statsmodels`, `scikit-learn`
* **Simulación y Ciencia:** `SciPy` (Monte Carlo)
* **Visualización:** `matplotlib`, `seaborn`
* **Business Intelligence:** Power BI Desktop (Modelado en estrella + DAX)

---

## 📂 Contenido del Repositorio

* `/Dashboard/` - Archivo fuente o documentación de la arquitectura del Cuadro de Mandos en Power BI.
* `app_tfm_final.py` - Script principal de ejecución y transformaciones ETL.
* `Analisis_y_Visualizacion.ipynb` - Jupyter Notebook con el Análisis Exploratorio de Datos (EDA) y entrenamiento de modelos.
* `/data/` - Datasets y matrices históricas armonizadas procedentes de Eurostat, OCDE (DIOC), INE y Banco de España.

---

## 📊 Principales Conclusiones Macroeconómicas
* **Efecto Palanca:** Por cada euro de reducción en el diferencial salarial horario con Europa, el modelo asocia una disminución estimada de ~22,000 personas en el stock de emigrantes cualificados.
* **Sesgo de Género:** Se identificó que el **57.6%** de los emigrantes cualificados son mujeres, lo que sitúa la brecha de género como un vector crítico para el diseño de futuras políticas públicas de retención de talento.