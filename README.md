# Supply Chain Lakehouse Project

## Obiettivo 🎯
Progetto portfolio orientato **Data Engineering** su Databricks con Python, PySpark e Delta Lake. L'architettura precede la scelta del dataset per garantire flessibilità e scalabilità. Un piccolo modulo ML arriverà solo alla fine, dopo aver costruito dati affidabili.

Questo sequencing segue il pattern lakehouse Databricks: prima dati trusted, poi analytics/ML.

## Contesto Aziendale 📊
Target: analytics supply chain per operations con visibilità su ordini, scorte, fornitori e spedizioni. Domande business tipiche:
- Ritardi fornitori
- Rischio stock-out  
- Performance spedizioni
- Costi per route
- Tassi difetti

Framing ideale per colloquio: pipeline operativa che produce tabelle pronte per dashboard e prediction leggera.

## Perché Data Engineering al 90% 🔧
Il valore NON è il modello finale. Il valore è:
- Ingestione raw da fonti eterogenee
- Schema enforcement e standardizzazione
- Controlli qualità con business rules
- Silver tables affidabili
- Gold tables pronte per consumo business

Perfetto per medallion architecture: bronze (raw), silver (validated), gold (curated).

## Architettura Proposta 🏗️

### Batch-First Lakehouse
Batch come default: più semplice da spiegare, testare e scalare. Estendibile a near-real-time dopo.
Bronze → raw CSV/API/ERP con metadata
↓ Silver → cleaned entities con quality checks
↓ Gold → KPI marts per analytics/ML

text

### Medallion Layers

**Bronze** (landing zone)
bronze_supply_chain_raw

raw CSV as-is

ingestion_ts, source_file, batch_id

text

**Silver** (business entities)
silver_supply_chain

SKU deduplicato

tipi castati

categorie normalizzate

record rejected flagged

text

**Gold** (KPI marts)
gold_supplier_performance
gold_inventory_risk
gold_shipping_kpis
gold_quality_summary

text

## Dataset Reale: supply_chain_data-2.csv 📊
**Source**: 1 CSV wide (~20 colonne) con SKU + metrics aggregate:
Product type | SKU | Price | Stock | Lead times | Supplier |
Inspection | Defect rates | Shipping costs | Routes | etc...

text

**Grain**: 1 riga per SKU/prodotto con attributi misti operations.

**Adattamento architettura**:
1 CSV → 1 bronze → 1 silver → 4 gold marts tematici

text
Non serve forzare normalizzazione 3NF enterprise.

## Data Quality Checks ✅
MANDATORY KEYS: SKU, Supplier name
NO NEGATIVI: Stock levels, Order quantities, Shipping costs
DUPLICATI: SKU uniqueness
CATEGORIE: trim/lower Product type, Supplier name, Routes
INSPECTION: Pass/Fail/Pending → binaria per ML
DUPLICATI COLONNE: Lead times vs Lead time → rename

text

## Gold KPIs da Costruire 📊
Supplier Performance: defect rate, avg lead time per supplier

Inventory Risk: stock vs reorder threshold

Shipping KPIs: cost/route, carrier performance

Quality Summary: Pass/Fail rate per supplier/product type

text

## Dove Va il Mini-ML 🤖
**Dopo** i gold tables, su dati curati:
Classificazione Inspection results (Pass/Fail)

Regressione Shipping costs per route/supplier

Stock-out risk prediction (stock basso + lead time lungo)

text

## Scelte Tecniche Databricks ⚙️
✓ Delta tables (ACID + time travel)
✓ Notebook orchestrator + Python modules
✓ Parametrizzazione paths/catalog
✓ Unity Catalog (se disponibile)
✗ No DLT/Streaming (fase 1)

text

## Struttura Cartelle 📁
supply_chain_lakehouse/
├── README.md
├── notebooks/
│ ├── 01_ingest_bronze.ipynb
│ ├── 02_silver_cleaning.ipynb
│ ├── 03_gold_kpis.ipynb
│ └── 04_ml_quality_prediction.ipynb
├── data/
│ └── supply_chain_data-2.csv
└── src/
├── config.py
├── schemas.py
└── quality_checks.py

text




## Implementation Roadmap 🚀
README + architettura definita

Bronze: ingest CSV → Delta raw

Silver: cleaning + quality → silver_supply_chain

Gold: 4 KPI marts tematici

ML: Inspection classification su gold_quality

Dashboard SQL views su gold tables
