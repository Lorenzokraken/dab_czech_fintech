# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Czech Fintech
# MAGIC
# MAGIC Ingestion raw da ADLS → Delta tables in czech_fintech.bronze
# MAGIC Nessun cast logico: tutto StringType. I cast vengono fatti in Silver.

# COMMAND ----------

from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import StructType, StructField, StringType

CATALOG       = "czech_fintech"
BRONZE_SCHEMA = "bronze"
STORAGE_ROOT  = "abfss://raw@czechfintechdata.dfs.core.windows.net"
STATIC_PATH   = f"{STORAGE_ROOT}/static"
TRANS_PATH    = f"{STORAGE_ROOT}/transactions"
CHECKPOINT    = f"{STORAGE_ROOT}/checkpoints/bronze_transactions"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema espliciti — tutti StringType
# MAGIC
# MAGIC Perché StringType ovunque: Bronze è un mirror fedele del CSV.
# MAGIC Se castiamo qui e un valore non converte, perdiamo la riga.
# MAGIC In Bronze non si perde niente — i cast vengono fatti in Silver con controllo esplicito.
# MAGIC
# MAGIC Note sui dati:
# MAGIC - district: header usa codici A1..A16, non nomi descrittivi (è il dataset originale)
# MAGIC - card.issued: ha formato "YYMMDD HH:MM:SS" — lasciamo stringa, Silver lo parserà
# MAGIC - client.birth_number: codice ceco YYMMDD o YYMM+50DD per donne — stringa, non data

# COMMAND ----------

schemas = {
    "account": StructType([
        StructField("account_id",   StringType()),  # PK
        StructField("district_id",  StringType()),  # FK → district
        StructField("frequency",    StringType()),  # "POPLATEK MESICNE" ecc
        StructField("date",         StringType()),  # YYMMDD — apertura conto
    ]),
    "client": StructType([
        StructField("client_id",    StringType()),  # PK
        StructField("birth_number", StringType()),  # YYMMDD (F: YYMM+50DD)
        StructField("district_id",  StringType()),  # FK → district
    ]),
    "card": StructType([
        StructField("card_id",  StringType()),  # PK
        StructField("disp_id",  StringType()),  # FK → disp
        StructField("type",     StringType()),  # classic / gold
        StructField("issued",   StringType()),  # "YYMMDD HH:MM:SS"
    ]),
    "disp": StructType([
        StructField("disp_id",    StringType()),  # PK
        StructField("client_id",  StringType()),  # FK → client
        StructField("account_id", StringType()),  # FK → account
        StructField("type",       StringType()),  # OWNER / DISPONENT
    ]),
    "district": StructType([
        StructField("A1",  StringType()),  # district_id (header originale)
        StructField("A2",  StringType()),  # nome distretto
        StructField("A3",  StringType()),  # regione
        StructField("A4",  StringType()),  # popolazione
        StructField("A5",  StringType()),  # comuni <499 abitanti
        StructField("A6",  StringType()),  # comuni 500-1999
        StructField("A7",  StringType()),  # comuni 2000-9999
        StructField("A8",  StringType()),  # comuni >10000
        StructField("A9",  StringType()),  # n° città
        StructField("A10", StringType()),  # % urbano
        StructField("A11", StringType()),  # salario medio
        StructField("A12", StringType()),  # tasso disoccupazione 1995
        StructField("A13", StringType()),  # tasso disoccupazione 1996
        StructField("A14", StringType()),  # n° imprenditori per 1000 ab
        StructField("A15", StringType()),  # crimini 1995
        StructField("A16", StringType()),  # crimini 1996
    ]),
    "loan": StructType([
        StructField("loan_id",    StringType()),  # PK
        StructField("account_id", StringType()),  # FK → account
        StructField("date",       StringType()),  # YYMMDD — erogazione
        StructField("amount",     StringType()),  # importo totale
        StructField("duration",   StringType()),  # mesi
        StructField("payments",   StringType()),  # rata mensile
        StructField("status",     StringType()),  # A/B/C/D
    ]),
    "order": StructType([
        StructField("order_id",    StringType()),  # PK
        StructField("account_id",  StringType()),  # FK → account
        StructField("bank_to",     StringType()),  # banca destinataria
        StructField("account_to",  StringType()),  # conto destinatario
        StructField("amount",      StringType()),  # importo
        StructField("k_symbol",    StringType()),  # causale (SIPO ecc)
    ]),
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestion Statici — Batch
# MAGIC
# MAGIC La funzione legge ogni CSV con schema esplicito e lo scrive come Delta table.
# MAGIC `mergeSchema=False` perché lo schema è sotto nostro controllo — se cambia, vogliamo saperlo subito.

# COMMAND ----------

def ingest_static(table_name, source_path, schema):
    df = (
        spark.read
            .option("header", "true")
            .option("sep", ";")
            .schema(schema)
            .csv(source_path)
            .withColumn("_ingestion_ts", current_timestamp())
    )
    (
        df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}")
    )
    count = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}").count()
    print(f"✅ {table_name}: {count} righe")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Esecuzione

# COMMAND ----------

for table_name, schema in schemas.items():
    ingest_static(
        table_name  = table_name,
        source_path = f"{STATIC_PATH}/{table_name}.csv",
        schema      = schema
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verifica

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'account'  AS tbl, COUNT(*) AS n FROM czech_fintech.bronze.account  UNION ALL
# MAGIC SELECT 'client',          COUNT(*)       FROM czech_fintech.bronze.client   UNION ALL
# MAGIC SELECT 'card',            COUNT(*)       FROM czech_fintech.bronze.card     UNION ALL
# MAGIC SELECT 'disp',            COUNT(*)       FROM czech_fintech.bronze.disp     UNION ALL
# MAGIC SELECT 'district',        COUNT(*)       FROM czech_fintech.bronze.district UNION ALL
# MAGIC SELECT 'loan',            COUNT(*)       FROM czech_fintech.bronze.loan     UNION ALL
# MAGIC SELECT 'order',           COUNT(*)       FROM czech_fintech.bronze.`order`
# MAGIC ORDER BY tbl;
