CREATE SCHEMA beijing_dw;

CREATE TABLE beijing_dw.dim_station (
    station_id SERIAL PRIMARY KEY,
    station_name VARCHAR(20) UNIQUE NOT NULL
);
CREATE TABLE beijing_dw.dim_time (
    time_id SERIAL PRIMARY KEY,
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    hour SMALLINT NOT NULL,
    ts TIMESTAMP NOT NULL,
    UNIQUE (year, month, day, hour)
);
CREATE TABLE beijing_dw.fact_datos (
    station_id INT NOT NULL,
    time_id INT NOT NULL,

    pm25 NUMERIC(10,2),
    pm10 NUMERIC(10,2),
    so2  NUMERIC(10,2),
    no2  NUMERIC(10,2),
    co   NUMERIC(10,2),
    o3   NUMERIC(10,2),
    temp NUMERIC(10,2),
    pres NUMERIC(10,2),
    dewp NUMERIC(10,2),
    rain NUMERIC(10,2),
    wd   VARCHAR(10),
    wspm NUMERIC(10,2),

    PRIMARY KEY (station_id, time_id),

    CONSTRAINT fk_station
        FOREIGN KEY (station_id)
        REFERENCES beijing_dw.dim_station(station_id),

    CONSTRAINT fk_time
        FOREIGN KEY (time_id)
        REFERENCES beijing_dw.dim_time(time_id)
);
CREATE TABLE beijing_dw.staging_datos (
    "No" INT,
    "year" SMALLINT,
    "month" SMALLINT,
    "day" SMALLINT,
    "hour" SMALLINT,
    "PM2.5" NUMERIC(10,2),
    "PM10" NUMERIC(10,2),
    "SO2" NUMERIC(10,2),
    "NO2" NUMERIC(10,2),
    "CO" NUMERIC(10,2),
    "O3" NUMERIC(10,2),
    "TEMP" NUMERIC(10,2),
    "PRES" NUMERIC(10,2),
    "DEWP" NUMERIC(10,2),
    "RAIN" NUMERIC(10,2),
    "wd" VARCHAR(10),
    "WSPM" NUMERIC(10,2),
    "station" VARCHAR(20)
);

-- Aotizhongxin
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Aotizhongxin_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Changping
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Changping_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Dingling
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dingling_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Dongsi
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dongsi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Guanyuan
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Guanyuan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Gucheng
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Gucheng_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Huairou
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Huairou_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Nongzhanguan
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Nongzhanguan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Shunyi
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Shunyi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tiantan
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Tiantan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Wanliu
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanliu_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Wanshouxigong
COPY beijing_dw.staging_datos
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanshouxigong_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';


INSERT INTO beijing_dw.dim_station (station_name)
SELECT DISTINCT station
FROM beijing_dw.staging_datos;

INSERT INTO beijing_dw.dim_time (year, month, day, hour, ts)
SELECT DISTINCT
    year,
    month,
    day,
    hour,
    make_timestamp(year, month, day, hour, 0, 0)
FROM beijing_dw.staging_datos;

INSERT INTO beijing_dw.fact_datos (
    station_id,
    time_id,
    pm25, pm10, so2, no2, co, o3,
    temp, pres, dewp, rain, wd, wspm
)
SELECT
    s.station_id,
    t.time_id,
    d."PM2.5",
    d."PM10",
    d."SO2",
    d."NO2",
    d."CO",
    d."O3",
    d."TEMP",
    d."PRES",
    d."DEWP",
    d."RAIN",
    d.wd,
    d."WSPM"
FROM beijing_dw.staging_datos d
JOIN beijing_dw.dim_station s
  ON s.station_name = d.station
JOIN beijing_dw.dim_time t
  ON (t.year, t.month, t.day, t.hour) =
     (d.year, d.month, d.day, d.hour);

CREATE INDEX idx_fact_station ON beijing_dw.fact_datos (station_id);
CREATE INDEX idx_fact_time ON beijing_dw.fact_datos (time_id);
CREATE INDEX idx_time_ts ON beijing_dw.dim_time (ts);

--Estaciones mas contaminadas en promedio

SELECT
    s.station_name AS station,
    ROUND(AVG(f.pm25), 2) AS avg_pm25,
    ROUND(AVG(f.pm10), 2) AS avg_pm10
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
GROUP BY s.station_name
ORDER BY avg_pm25 DESC;

--ESTACIONES URBANAS VS EXTRARRADIO

SELECT
    CASE
        WHEN s.station_name IN ('Dongsi','Guanyuan','Aotizhongxin','Tiantan') THEN 'URBANA'
        WHEN s.station_name IN ('Dingling','Huairou','Changping') THEN 'EXTERIOR'
    END AS ubicacion,
    ROUND(AVG(f.no2), 2) AS no2_coches,
    ROUND(AVG(f.pm25), 2) AS pm25_total,
    ROUND(AVG(f.pm10), 2) AS pm10_total,
    ROUND(AVG(f.wspm), 2) AS velocidad_viento
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
WHERE s.station_name IN
 ('Dongsi','Guanyuan','Aotizhongxin','Tiantan','Dingling','Huairou','Changping')
GROUP BY 1;


--CÓMO IMPACTA EL VIENTO

SELECT
    CASE
        WHEN f.wspm < 1 THEN 'Calma (0-1 m/s)'
        WHEN f.wspm BETWEEN 1 AND 3 THEN 'Brisa Ligera (1-3 m/s)'
        ELSE 'Viento Fuerte (>3 m/s)'
    END AS categoria_viento,
    ROUND(AVG(f.pm25), 2) AS avg_pm25
FROM beijing_dw.fact_datos f
GROUP BY 1
ORDER BY avg_pm25 DESC;

--¿ES EL VIENTO ÚTIL?

SELECT
    s.station_name AS station,
    ROUND(AVG(f.wspm), 2) AS velocidad_viento,
    ROUND(AVG(f.pm25), 2) AS media_pm25,
    ROUND(AVG(f.pm10), 2) AS media_pm10,
    ROUND(AVG(f.pm25) / NULLIF(AVG(f.wspm),0), 2) AS estancamiento_pm25,
    ROUND(AVG(f.pm10) / NULLIF(AVG(f.wspm),0), 2) AS estancamiento_pm10
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
GROUP BY s.station_name
ORDER BY estancamiento_pm25 DESC;

--📈 EVOLUCIÓN DE LA CONTAMINACIÓN

SELECT
    t.year,
    ROUND(AVG(f.pm25), 2) AS media_anual_pm25,
    MAX(f.pm25) AS pico_maximo
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
GROUP BY t.year
ORDER BY t.year;

--CONTAMINACIÓN POR HORA

SELECT
    t.hour,
    ROUND(AVG(f.pm25), 2) AS avg_pm25
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
GROUP BY t.hour
ORDER BY t.hour;

--CONTAMINACIÓN POR ESTACIÓN DEL AÑO

SELECT
    CASE
        WHEN t.month IN (12,1,2) THEN 'Invierno'
        WHEN t.month IN (3,4,5) THEN 'Primavera'
        WHEN t.month IN (6,7,8) THEN 'Verano'
        WHEN t.month IN (9,10,11) THEN 'Otoño'
    END AS estacion,
    ROUND(AVG(f.pm25),2) AS media_pm25
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
GROUP BY 1
ORDER BY media_pm25 DESC;

--MEDIAS MÓVILES PM2.5
SELECT
    s.station_name AS station,
    t.ts,
    f.pm25,
    AVG(f.pm25) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
      RANGE BETWEEN INTERVAL '23 hours' PRECEDING AND CURRENT ROW
    ) AS pm25_ma24h,
    AVG(f.pm25) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
      RANGE BETWEEN INTERVAL '71 hours' PRECEDING AND CURRENT ROW
    ) AS pm25_ma72h
FROM beijing_dw.fact_datos f
JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
WHERE f.pm25 IS NOT NULL;

--DÍAS QUE SUPERAN UMBRALES

WITH daily AS (
  SELECT
    s.station_name AS station,
    date_trunc('day', t.ts)::date AS d,
    AVG(f.pm25) AS pm25_day
  FROM beijing_dw.fact_datos f
  JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
  JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
  GROUP BY 1,2
)
SELECT
  station,
  COUNT(*) AS days_total,
  SUM((pm25_day > 15)::int) AS days_exceed_who_15,
  ROUND(100.0 * SUM((pm25_day > 15)::int) / COUNT(*),2) AS pct_exceed_who,
  SUM((pm25_day > 75)::int) AS days_exceed_china_75,
  ROUND(100.0 * SUM((pm25_day > 75)::int) / COUNT(*),2) AS pct_exceed_china
FROM daily
GROUP BY station
ORDER BY pct_exceed_who DESC;

--DETECCIÓN DE EPISODIOS (>150 µg/m³)

WITH flagged AS (
  SELECT
    s.station_name AS station,
    t.ts,
    f.pm25,
    (f.pm25 > 150) AS exceed
  FROM beijing_dw.fact_datos f
  JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
  JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
),
islands AS (
  SELECT *,
    ts - ROW_NUMBER() OVER (PARTITION BY station ORDER BY ts) * INTERVAL '1 hour' AS grp
  FROM flagged
  WHERE exceed
)
SELECT
  station,
  MIN(ts) AS episode_start,
  MAX(ts) AS episode_end,
  COUNT(*) AS hours_duration,
  MAX(pm25) AS peak_pm25,
  ROUND(AVG(pm25),2) AS avg_pm25
FROM islands
GROUP BY station, grp
HAVING COUNT(*) >= 6
ORDER BY hours_duration DESC, peak_pm25 DESC;

WITH lluvia_ctx AS (
  SELECT
    s.station_name AS station,
    t.ts,
    f.rain,
    f.pm10,

    -- antes
    LAG(f.pm10, 1) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
    ) AS pm10_before,

    -- después (corto plazo)
    LEAD(f.pm10, 1) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
    ) AS pm10_after_1h,

    -- medio plazo
    LEAD(f.pm10, 72) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
    ) AS pm10_after_3d,

    LEAD(f.pm10, 120) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
    ) AS pm10_after_5d,

    LEAD(f.pm10, 168) OVER (
      PARTITION BY s.station_name
      ORDER BY t.ts
    ) AS pm10_after_7d

  FROM beijing_dw.fact_datos f
  JOIN beijing_dw.dim_station s ON f.station_id = s.station_id
  JOIN beijing_dw.dim_time t ON f.time_id = t.time_id
  WHERE f.pm10 IS NOT NULL
)
SELECT
  station,
  ROUND(AVG(pm10_before), 2)   AS pm10_before_rain,
  ROUND(AVG(pm10), 2)          AS pm10_during_rain,
  ROUND(AVG(pm10_after_1h), 2) AS pm10_after_1h,
  ROUND(AVG(pm10_after_3d), 2) AS pm10_after_3d,
  ROUND(AVG(pm10_after_5d), 2) AS pm10_after_5d,
  ROUND(AVG(pm10_after_7d), 2) AS pm10_after_7d
FROM lluvia_ctx
WHERE rain > 0
GROUP BY station
ORDER BY station;

--El análisis se ha realizado considerando todos los episodios de lluvia, 
--sin distinguir entre eventos aislados y periodos consecutivos de precipitación. 
--Este enfoque permite evaluar el efecto agregado de la lluvia en condiciones reales, 
--aunque no permite atribuir la persistencia observada a un único evento individual. 

