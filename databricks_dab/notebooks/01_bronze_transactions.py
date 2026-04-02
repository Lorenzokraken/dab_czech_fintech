# Databricks notebook source

import pyspark.sql.functions as F

CATALOG       = "czech_fintech"
BRONZE_SCHEMA = "bronze"
STORAGE_ROOT  = "abfss://raw@czechfintechdata.dfs.core.windows.net"
TRANS_PATH    = f"{STORAGE_ROOT}/transactions"
CHECKPOINT    = f"{STORAGE_ROOT}/checkpoints/bronze_transactions"
SCHEMA_LOC    = f"{STORAGE_ROOT}/checkpoints/bronze_transactions_schema"

# COMMAND ----------

def ingest_transactions():
    query = (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("header", True)
            .option("sep", ";")
            .option("inferSchema", True)
            .load(TRANS_PATH)
            .toDF(
                "trans_id", "account_id", "date", "type", "operation",
                "amount", "balance", "k_symbol", "bank", "account"
            )
            .withColumn("_ingestion_ts", F.current_timestamp())
            .withColumn("date_parsed", F.to_date(
                F.concat(F.lit("19"), F.col("date").cast("string")), "yyyyMMdd"
            ))
            .withColumn("year",  F.year(F.col("date_parsed")))
            .withColumn("month", F.month(F.col("date_parsed")))
            .writeStream
            .format("delta")
            .outputMode("append")
            .trigger(availableNow=True)
            .option("checkpointLocation", CHECKPOINT)
            .partitionBy("year", "month")
            .toTable(f"{CATALOG}.{BRONZE_SCHEMA}.transactions")
    )
    query.awaitTermination()

# COMMAND ----------

# Pulisci checkpoint prima di rilanciare (esegui solo se rilanci da zero)
# dbutils.fs.rm(CHECKPOINT, recurse=True)
# dbutils.fs.rm(SCHEMA_LOC, recurse=True)

# COMMAND ----------

ingest_transactions()

# COMMAND ----------

print(spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.transactions").count())
