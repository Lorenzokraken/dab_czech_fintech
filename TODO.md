# Czech Fintech — TODO / Fix List

---

## BRONZE
<!-- 
### B1 — Allineare DDL con metadati reali
**File:** `00_schema.ipynb`
Il DDL crea le tabelle senza `_ingestion_ts` e `_source_file`, ma l'ingestion le aggiunge.
Il DDL deve essere la fonte di verità.

```sql
-- Aggiungere a ogni CREATE TABLE in 00_schema.ipynb:
_ingestion_ts  TIMESTAMP,
_source_file   STRING
``` -->

### B2 — Aggiungere `_source_file` all'ingestion statica
**File:** `01_bronze_static.py`

```python
# # Prima (manca _source_file):
# spark.read.csv(source_path, header=True, sep=";") \
#     .withColumn("_ingestion_ts", current_timestamp())

# # Dopo:
# spark.read.csv(source_path, header=True, sep=";") \
#     .withColumn("_ingestion_ts", current_timestamp()) \
#     .withColumn("_source_file", lit(source_path))
```
<!-- 
### B3 — Aggiungere `_source_file` alle transazioni (Auto Loader)
**File:** `02_bronze_transaction.ipynb`
Auto Loader espone il path del file via `_metadata.file_path`.

```python
# Aggiungere nel readStream dopo le select delle colonne:
.withColumn("_source_file", F.col("_metadata.file_path"))
# Nota: _metadata è disponibile solo su readStream con cloudFiles o text/csv format
``` -->
<!-- 
### B4 — Rimuovere `mergeSchema=true` dall'overwrite statica
**File:** `01_bronze_static.py`
Pericoloso in produzione: uno schema drift silenzioso rompe la pipeline downstream.

```python
# Togliere mergeSchema=true:
.write.mode("overwrite").saveAsTable(...)
``` -->

---

## SILVER

### S1 — Drop + ricrea tabelle silver prima di riscrivere
Da eseguire una volta per pulizia prima di reimplementare silver.

<!-- ```python
CATALOG = "czech_fintech"
SILVER = "silver"
tables = ["transactions", "account", "client", "card", "disp", "district", "loan", "order"]
for t in tables:
    spark.sql(f"DROP TABLE IF EXISTS {CATALOG}.{SILVER}.{t}")
print("✅ Silver tables dropped")
``` -->

### S2 — Implementare typing su transactions
**File:** `04_silver.ipynb` — attualmente è un passthrough senza cast.

```python
from pyspark.sql.functions import col, to_date, concat, lit, when, substring, year, month
from pyspark.sql.types import IntegerType, DecimalType

def parse_czech_date(col_name):
    c = col(col_name)
    return to_date(
        when(substring(c, 1, 2).cast(IntegerType()) < 50, concat(lit("20"), c))
        .otherwise(concat(lit("19"), c)),
        "yyyyMMdd"
    )

trans_silver = (
    spark.table(f"{CATALOG}.{BRONZE}.transactions")
    .drop("_ingestion_ts", "_source_file")
    .withColumn("date",    parse_czech_date("date"))
    .withColumn("amount",  col("amount").cast(DecimalType(15,2)))
    .withColumn("balance", col("balance").cast(DecimalType(15,2)))
    .withColumn("year",    year(col("date")))
    .withColumn("month",   month(col("date")))
    .withColumn("_silver_ts", current_timestamp())
)
```

### S3 — Join transactions → account → disp → client → district
**File:** `04_silver.ipynb`
Il join va fatto via `disp` (bridge account–client) prendendo solo il titolare (`type = 'OWNER'`).

```python
disp_owner = (
    spark.table(f"{CATALOG}.{BRONZE}.disp")
    .filter(col("type") == "OWNER")
    .select("account_id", "client_id")
)

trans_silver = (
    trans_silver
    .join(disp_owner, "account_id", "left")
)
# Risultato: transactions ha client_id popolato
```

### S4 — Decodifica birth_number su client
**File:** `04_silver.ipynb`
`birth_number` è nel formato `YYMM(+50)DD/XXXX`. Donne hanno MM+50.

```python
from pyspark.sql.functions import expr

client_silver = (
    spark.table(f"{CATALOG}.{BRONZE}.client")
    .drop("_ingestion_ts", "_source_file")
    .withColumn("gender",
        when(substring(col("birth_number"), 3, 2).cast(IntegerType()) > 50, lit("F"))
        .otherwise(lit("M"))
    )
    .withColumn("birth_month_raw", substring(col("birth_number"), 3, 2).cast(IntegerType()))
    .withColumn("birth_month", when(col("birth_month_raw") > 50, col("birth_month_raw") - 50).otherwise(col("birth_month_raw")))
    .withColumn("birth_date",
        to_date(
            concat(
                lit("19"), substring(col("birth_number"), 1, 2),
                lpad(col("birth_month").cast(StringType()), 2, "0"),
                substring(col("birth_number"), 5, 2)
            ), "yyyyMMdd"
        )
    )
    .withColumn("_silver_ts", current_timestamp())
)
```

### S5 — Cast tipizzati su loan e order
**File:** `04_silver.ipynb`

```python
loan_silver = (
    spark.table(f"{CATALOG}.{BRONZE}.loan")
    .drop("_ingestion_ts", "_source_file")
    .withColumn("date",     parse_czech_date("date"))
    .withColumn("amount",   col("amount").cast(DecimalType(15,2)))
    .withColumn("duration", col("duration").cast(IntegerType()))
    .withColumn("payments", col("payments").cast(DecimalType(15,2)))
    .withColumn("_silver_ts", current_timestamp())
)

order_silver = (
    spark.table(f"{CATALOG}.{BRONZE}.order")
    .drop("_ingestion_ts", "_source_file")
    .withColumn("amount", col("amount").cast(DecimalType(15,2)))
    .withColumn("_silver_ts", current_timestamp())
)
```

### S6 — SCD Type 2 su account.frequency
**File:** `04_silver.ipynb`
`account.frequency` può cambiare nel tempo. Ogni cambio genera una nuova riga.

```python
from delta.tables import DeltaTable
from pyspark.sql.functions import current_date

# Prima esecuzione (init): scrivi con valid_from/valid_to/is_current
account_incoming = (
    spark.table(f"{CATALOG}.{BRONZE}.account")
    .drop("_ingestion_ts", "_source_file")
    .withColumn("date", parse_czech_date("date"))
    .withColumn("valid_from", current_date())
    .withColumn("valid_to",   lit(None).cast(DateType()))
    .withColumn("is_current", lit(True))
    .withColumn("_silver_ts", current_timestamp())
)

# MERGE per run incrementali (SCD Type 2)
# Chiude la riga corrente se frequency è cambiata, inserisce la nuova
if spark.catalog.tableExists(f"{CATALOG}.{SILVER}.account"):
    dt = DeltaTable.forName(spark, f"{CATALOG}.{SILVER}.account")
    dt.alias("existing").merge(
        account_incoming.alias("incoming"),
        "existing.account_id = incoming.account_id AND existing.is_current = true"
    ).whenMatchedUpdate(
        condition="existing.frequency != incoming.frequency",
        set={"valid_to": "current_date()", "is_current": "false"}
    ).execute()

    account_incoming.join(
        spark.table(f"{CATALOG}.{SILVER}.account").filter(col("is_current")),
        "account_id", "left_anti"
    ).write.mode("append").saveAsTable(f"{CATALOG}.{SILVER}.account")
else:
    account_incoming.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SILVER}.account")
```

### S7 — Aggiungere `_silver_ts` a tutte le tabelle passthrough
Account, client, card, disp, district già coperti negli step precedenti.
Verificare che ogni `.withColumn("_silver_ts", current_timestamp())` sia presente prima del write.

---

## GOLD

### G1 — Fix bug runtime: definire CATALOG/GOLD prima del DROP
**File:** `06_gold.ipynb` — cella 0 usa variabili non ancora definite.

```python
# Mettere SEMPRE le variabili nella prima cella, prima di qualsiasi DROP:
CATALOG = "czech_fintech"
SILVER  = "silver"
GOLD    = "gold"

for t in ["loan_risk_summary", "account_kpi", "transaction_trends"]:
    spark.sql(f"DROP TABLE IF EXISTS {CATALOG}.{GOLD}.{t}")
```

### G2 — Fix join district in loan_risk_summary
**File:** `06_gold.ipynb`
Il join su `A1 == district_id` può fallire per trailing spaces o tipo inconsistente.

```python
# Forzare trim + cast esplicito su entrambi i lati del join:
district_clean = district.select(
    col("A1").cast("int").alias("district_id"),
    col("A2").alias("district_name")
)
account_clean = account.select(
    col("account_id"),
    col("district_id").cast("int")
)
# Poi joinare su int, non su string
```

### G3 — Implementare account_kpi
**File:** `06_gold.ipynb` — tabella mancante.

```python
from pyspark.sql.functions import col, sum, avg, count, year, month

trans = spark.table(f"{CATALOG}.{SILVER}.transactions")

account_kpi = (
    trans
    .groupBy("account_id", "year", "month")
    .agg(
        sum(when(col("type") == "PRIJEM", col("amount")).otherwise(0)).alias("total_credit"),
        sum(when(col("type") == "VYDAJ",  col("amount")).otherwise(0)).alias("total_debit"),
        avg("balance").alias("avg_balance"),
        count("trans_id").alias("n_transactions")
    )
)

account_kpi.write.mode("overwrite").saveAsTable(f"{CATALOG}.{GOLD}.account_kpi")
print(f"✅ account_kpi: {spark.table(f'{CATALOG}.{GOLD}.account_kpi').count()} rows")
```

### G4 — Implementare transaction_trends
**File:** `06_gold.ipynb` — tabella mancante.

```python
from pyspark.sql.functions import col, avg, count, first

trans = spark.table(f"{CATALOG}.{SILVER}.transactions")
account = spark.table(f"{CATALOG}.{SILVER}.account")
district = spark.table(f"{CATALOG}.{SILVER}.district")

district_clean = district.select(
    col("A1").alias("district_id"),
    col("A2").alias("district_name"),
    col("A3").alias("region")
)

trends = (
    trans
    .join(account.select("account_id", "district_id"), "account_id", "left")
    .join(district_clean, "district_id", "left")
    .groupBy("district_id", "district_name", "region", "year", "month")
    .agg(
        count("trans_id").alias("n_transactions"),
        avg("amount").alias("avg_amount"),
        sum(when(col("type") == "PRIJEM", col("amount")).otherwise(0)).alias("total_credit"),
        sum(when(col("type") == "VYDAJ",  col("amount")).otherwise(0)).alias("total_debit")
    )
)

trends.write.mode("overwrite").saveAsTable(f"{CATALOG}.{GOLD}.transaction_trends")
print(f"✅ transaction_trends: {spark.table(f'{CATALOG}.{GOLD}.transaction_trends').count()} rows")
```

---

## DAB

### D1 — Configurare job nel bundle
**File:** `databricks_dab/databricks.yml` o `job.json`
Aggiungere task in sequenza:

```
schema → bronze_static → bronze_transactions → silver → gold
```

Con dipendenze esplicite (`depends_on`) tra i task.

---

## Riepilogo priorità

| # | Fix | Impatto |
|---|-----|---------|
| S1 | Drop silver tables | Prerequisito |
| S2 | Typing transactions | Critico |
| S3 | Join trans→client via disp | Critico |
| S4 | Decodifica birth_number | Medio |
| S5 | Cast loan/order | Medio |
| S6 | SCD Type 2 account | Alto (portfolio) |
| S7 | _silver_ts ovunque | Basso |
| G1 | Fix bug CATALOG/GOLD | Critico (runtime error) |
| G2 | Fix join district | Medio |
| G3 | account_kpi | Alto |
| G4 | transaction_trends | Alto |
| B1-B4 | Bronze metadata/DDL | Basso |
