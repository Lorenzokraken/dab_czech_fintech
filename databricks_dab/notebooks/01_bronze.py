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
# MAGIC ## 0. Configurazione
# MAGIC
# MAGIC Centralizza qui tutti i path e i nomi.
# MAGIC Se cambia lo storage o il catalog, modifichi solo questa cella.
# MAGIC Queste variabili saranno poi parametrizzabili via DAB widgets.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Ingestion Statici — Batch
# MAGIC
# MAGIC I 7 file statici (account, client, card, disp, district, loan, order)
# MAGIC vengono letti con `read_files()` e scritti come Delta table in modalità `overwrite`.
# MAGIC
# MAGIC Sono dati dimensionali stabili — overwrite è sufficiente, non serve CDC.
# MAGIC
# MAGIC **Cose da sapere prima di scrivere il codice:**
# MAGIC - Separatore CSV: `;` (non virgola)
# MAGIC - Tutti i valori categorici sono in ceco (PRIJEM, VYDAJ, ecc.) — lasciali as-is in Bronze
# MAGIC - Il campo `date` nelle transazioni è formato YYMMDD (es. 930101 = 1 gen 1993) — NON parsarlo qui, lo farai in Silver
# MAGIC - Aggiungi sempre `_ingestion_ts` (current_timestamp) e `_source_file` (input_file_name)
# MAGIC
# MAGIC **Docs:**
# MAGIC - read_files: https://docs.databricks.com/en/sql/language-manual/functions/read_files.html
# MAGIC - withColumn / current_timestamp: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html

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

# COMMAND ----------

df = spark.sql(f"SELECT * FROM {CATALOG}.{BRONZE_SCHEMA}.account LIMIT 10")
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Ingestion Transazioni — Auto Loader
# MAGIC
# MAGIC Le transazioni (trans_0.csv ... trans_105.csv) vengono ingerate con Auto Loader
# MAGIC in modalità `trigger(availableNow=True)`: legge tutti i file disponibili al momento
# MAGIC dell'esecuzione e si ferma — comportamento batch ma con tracking incrementale.
# MAGIC
# MAGIC **Perché Auto Loader e non spark.read normale?**
# MAGIC Auto Loader mantiene un checkpoint su ADLS che traccia quali file ha già processato.
# MAGIC Se domani carichi altri 10 CSV nella cartella transactions/, riesegui il notebook
# MAGIC e lui legge SOLO i nuovi. Con spark.read rileggeresti tutto da capo ogni volta.
# MAGIC Questo simula un pattern di ingestion incrementale reale (es. feed giornaliero).
# MAGIC
# MAGIC **Partizionamento:**
# MAGIC Il campo `date` è YYMMDD (stringa). Devi estrarre year e month per partizionare.
# MAGIC Esempio: "930101" → year=1993, month=1
# MAGIC Hint: puoi usare substring() + cast() oppure to_date() con format "yyMMdd"
# MAGIC
# MAGIC **Docs:**
# MAGIC - Auto Loader: https://docs.databricks.com/en/ingestion/cloud-object-storage/auto-loader/index.html
# MAGIC - trigger(availableNow): https://docs.databricks.com/en/structured-streaming/triggers.html
# MAGIC - partitionBy: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.partitionBy.html

# COMMAND ----------

def ingest_transactions():
    spark.readStream.format("cloudFiles") \
        .option("cloudFiles.format", "csv") \
        .option("header", True) \
        .option("sep", ";") \
        .option("inferSchema", True) \
        .load("/mnt/landing/transactions") \
        .withColumn("_ingestion_ts", F.current_timestamp()) \
        .withColumn("date", F.to_date(F.col("date"), "YYMMDD")) \
        .withColumn("year", F.year(F.col("date"))) \
        .withColumn("month", F.month(F.col("date"))) \
        .writeStream \
        .format("delta") \
        .outputMode("append") \
        .trigger(availableNow=True) \
        .option("checkpointLocation", CHECKPOINT) \
        .partitionBy("year", "month") \
        .table(f"{CATALOG}.{BRONZE_DB}.transactions")
ingest_transactions()
spark.table(f"{CATALOG}.{BRONZE_DB}.transactions").count()



# La funzione deve:
# 1. Usare spark.readStream con format="cloudFiles"
#    - cloudFiles.format = "csv"
#    - header = true, sep = ";"
#    - inferSchema = true (o definisci schema esplicito se preferisci)
# 2. Aggiungere _ingestion_ts
# 3. Parsare il campo date (YYMMDD) ed estrarre colonne year e month
#    (servono per partitionBy — NON per logica business, quello è compito di Silver)
# 4. Scrivere in streaming con:
#    - format = "delta"
#    - outputMode = "append"
#    - trigger(availableNow=True)
#    - checkpointLocation = CHECKPOINT
#    - partitionBy("year", "month")
#    - table("czech_fintech.bronze.transactions")
# 5. Chiamare .awaitTermination() per aspettare che il job finisca
#
# Atteso dopo l'esecuzione:
# - Delta table czech_fintech.bronze.transactions
# - Partizionata per year/month (1993-1998 circa)
# - Solo i 3 CSV caricati ora. Se ne aggiungi altri e riesegui → solo i nuovi vengono letti
# - Verifica con: spark.table("czech_fintech.bronze.transactions").count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Verifica finale
# MAGIC
# MAGIC Esegui questa cella dopo aver completato le sezioni 1 e 2.
# MAGIC Controlla che tutte le tabelle esistano e abbiano righe.

# COMMAND ----------

# TODO: scrivi una cella di verifica che:
# 1. Fa un loop su tutte le 8 tabelle bronze (7 statici + transactions)
# 2. Per ognuna stampa: nome tabella, numero righe, colonne presenti
#
# Hint: spark.catalog.tableExists("czech_fintech.bronze.account")
# Hint: spark.table("...").count()
#
# Atteso:
# bronze.account      → ~4500 righe
# bronze.client       → ~5369 righe
# bronze.card         → ~892 righe
# bronze.disp         → ~5369 righe
# bronze.district     → ~77 righe
# bronze.loan         → ~682 righe
# bronze.order        → ~6471 righe
# bronze.transactions → subset dei 3 CSV caricati (verifica con count)

