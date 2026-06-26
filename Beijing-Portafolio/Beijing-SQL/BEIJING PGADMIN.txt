-- 1. Crear Schema 
CREATE SCHEMA calidad_aire_beijing;

-- 2. Crear Tabla
CREATE TABLE calidad_aire_beijing.datos (
    "No" INT,
    "year" SMALLINT NOT NULL,
    "month" SMALLINT NOT NULL,
    "day" SMALLINT NOT NULL,
    "hour" SMALLINT NOT NULL,
    "PM2.5" REAL,
    "PM10" REAL,
    "SO2" REAL,
    "NO2" REAL,
    "CO" REAL,
    "O3" REAL,
    "TEMP" REAL,
    "PRES" REAL,
    "DEWP" REAL,
    "RAIN" REAL,
    "wd" VARCHAR(10),
    "WSPM" REAL,
    "station" VARCHAR(20) NOT NULL,
    PRIMARY KEY ("station", "year", "month", "day", "hour")
);

-- 3. Carga de Datos
-- 3.1. Aotizhongxin
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Aotizhongxin_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.2. Changping
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Changping_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.3. Dingling
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dingling_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';
-- 3.4. Dongsi
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dongsi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.5. Guanyuan
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Guanyuan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.6. Gucheng
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Gucheng_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.7. Huairou
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Huairou_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.8. Nongzhanguan
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Nongzhanguan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.9. Shunyi
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Shunyi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.10. Tiantan
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Tiantan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.11. Wanliu
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanliu_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- 3.12. Wanshouxigong
COPY calidad_aire_beijing.datos ("No","year","month","day","hour","PM2.5","PM10",
"SO2","NO2","CO","O3","TEMP","PRES","DEWP","RAIN","wd","WSPM","station") 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanshouxigong_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';