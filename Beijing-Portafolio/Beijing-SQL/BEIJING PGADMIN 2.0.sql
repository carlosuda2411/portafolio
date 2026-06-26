-- Crear Schema 
CREATE SCHEMA calidad_aire_beijing;

-- Tabla Principal 
CREATE TABLE calidad_aire_beijing.datos 
    ("No" INT,
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
    PRIMARY KEY ("year", "month", "day", "hour"));

-- Tabla Aotizhongxin
CREATE TABLE calidad_aire_beijing.aotizhongxin 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
--"Crea la nueva tabla (aotizhongxin) basándote completamente en la estructura de la tabla de 
--referencia (calidad_aire_beijing.datos), e incluye todos los elementos de definición avanzados de esa tabla."
COPY calidad_aire_beijing.aotizhongxin 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Aotizhongxin_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Changping
CREATE TABLE calidad_aire_beijing.Changping
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Changping  
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Changping_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Dingling
CREATE TABLE calidad_aire_beijing.Dingling 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Dingling 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dingling_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Dongsi
CREATE TABLE calidad_aire_beijing.Dongsi 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Dongsi 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Dongsi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Guanyuan
CREATE TABLE calidad_aire_beijing.Guanyuan 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Guanyuan 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Guanyuan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Gucheng
CREATE TABLE calidad_aire_beijing.Gucheng 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Gucheng 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Gucheng_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Huairou
CREATE TABLE calidad_aire_beijing.Huairou 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Huairou 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Huairou_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Nongzhanguan
CREATE TABLE calidad_aire_beijing.Nongzhanguan
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Nongzhanguan 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Nongzhanguan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Shunyi
CREATE TABLE calidad_aire_beijing.Shunyi
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Shunyi 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Shunyi_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Tiantan
CREATE TABLE calidad_aire_beijing.Tiantan 
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Tiantan 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Tiantan_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Wanliu
CREATE TABLE calidad_aire_beijing.Wanliu
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Wanliu 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanliu_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';

-- Tabla Wanshouxigong
CREATE TABLE calidad_aire_beijing.Wanshouxigong
(LIKE calidad_aire_beijing.datos INCLUDING ALL);
	
COPY calidad_aire_beijing.Wanshouxigong 
FROM 'C:\beijing+multi+site+air+quality+data\PRSA2017_Data_20130301-20170228\PRSA_Data_20130301-20170228\PRSA_Data_Wanshouxigong_20130301-20170228.csv'
DELIMITER ','
CSV HEADER
NULL 'NA';