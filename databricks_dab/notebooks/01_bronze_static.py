# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Czech Fintech
# MAGIC
# MAGIC Questo notebook gestisce l'ingestion raw nel layer Bronze.
# MAGIC Nessuna trasformazione logica: i dati arrivano as-is dalla landing zone ADLS.
# MAGIC Si aggiungono solo colonne di metadata tecnico (_ingestion_ts, _source_file).
# MAGIC
# MAGIC **Input:**  `abfss://raw@czechfintechdata.dfs.core.windows.net/`
# MAGIC **Output:** `czech_fintech.bronze.*` (Delta tables)
# MAGIC
# MAGIC Tabelle prodotte:
# MAGIC - `bronze.account`, `bronze.client`, `bronze.card`
# MAGIC - `bronze.disp`, `bronze.district`, `bronze.loan`, `bronze.order`
# MAGIC - `bronze.transactions` (Auto Loader, partizionata per year/month)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Ingestion Statici — Batch
# MAGIC
# MAGIC I 7 file statici (account, client, card, disp, district, loan, order)
# MAGIC vengono letti con `read_files()` e scritti come Delta table in modalità `overwrite`.

# COMMAND ----------

from pyspark.sql.functions import current_timestamp

CATALOG       = "czech_fintech"
BRONZE_SCHEMA = "bronze"
STORAGE_ROOT  = "abfss://raw@czechfintechdata.dfs.core.windows.net"
STATIC_PATH   = f"{STORAGE_ROOT}/static"
TRANS_PATH    = f"{STORAGE_ROOT}/transactions"
CHECKPOINT    = f"{STORAGE_ROOT}/checkpoints/bronze_transactions"

def ingest_static(table_name, source_path):
    spark.read.csv(source_path, header=True, sep=";").withColumn("_ingestion_ts", current_timestamp()).write.mode("overwrite").option("mergeSchema", "true").saveAsTable(f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}")

tables = ["account",
          "client",
          "card",
          "disp",
          "district",
          "loan",
          "order"]


for table in tables:
    ingest_static(table, f"{STATIC_PATH}/{table}.csv")
