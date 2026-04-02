# Czech Fintech - Data Engineering Portfolio Project

## Stack
- Azure Databricks (Premium) + Unity Catalog
- ADLS Gen2 (czechfintechdata)
- Delta Lake Bronze → Silver → Gold
- Auto Loader (cloudFiles) per ingestione incrementale trans
- Databricks Asset Bundle (DAB) per orchestrazione
- Terraform (azurerm ~4.0, databricks ~1.40, azuread ~2.47) per IaC

## Architettura
```
ADLS Gen2: abfss://raw@czechfintechdata.dfs.core.windows.net/
└── raw/
    ├── static/       ← account, client, card, disp, district, loan, order
    ├── transactions/ ← trans_0.csv ... trans_105.csv (drop incrementale)
    └── checkpoints/  ← bronze_transactions (Auto Loader state)

Databricks: adb-7405607744677493.13.azuredatabricks.net
└── czech_fintech (catalog)
    ├── bronze  → ingestion raw as-is ✅
    ├── silver  → join, typing, SCD Type 2
    └── gold    → loan_risk_summary, account_kpi, transaction_trends
```

## Risorse Azure
| Risorsa | Nome | Note |
|---|---|---|
| Resource Group | li-rg | - |
| Databricks Service | databricks-czech-fintech | adb-7405607744677493.13 |
| Storage Account (dati) | czechfintechdata | ADLS Gen2, HNS enabled |
| Storage Account (managed) | dbstorage7rd45tfsb33gi | gestito da Databricks |
| Container | raw | abfss://raw@czechfintechdata.dfs.core.windows.net/ |
| Service Principal | sp-czech-fintech-databricks | id: 05fa7e2d-9c9a-4779-b0d2-e6f1fd18d886 |
| Access Connector | ac-czech-fintech-databricks | managed identity per Unity Catalog |

## Stato
- [x] Resource Group Azure (li-rg)
- [x] Databricks workspace Premium
- [x] Storage Account ADLS Gen2 (czechfintechdata) + container raw
- [x] Service Principal + role assignment (Storage Blob Data Contributor)
- [x] Access Connector for Azure Databricks (ac-czech-fintech-databricks)
- [x] Terraform per infrastruttura Azure (azure/)
- [x] Upload file statici → raw/static/
- [x] External Location configurata da Databricks UI
- [x] Catalog czech_fintech + schemi bronze/silver/gold creati
- [x] Bronze: 7 tabelle statiche (schema esplicito StringType, overwrite)
- [x] Bronze: transactions via Auto Loader (schema esplicito, checkpoint su ADLS)
- [x] Bronze: verifica completa (count + assert su tutte le 8 tabelle)
- [ ] Silver: join, cast, SCD Type 2
- [ ] Gold: loan_risk_summary, account_kpi, transaction_trends
- [ ] DAB orchestrazione

## Notebook
| File | Scopo |
|---|---|
| 00_schema.py | DDL SQL delle tabelle bronze (StringType, no LOCATION) |
| 01_bronze_static.py | Ingestion batch 7 file statici |
| 01_bronze_transactions.py | Ingestion Auto Loader transazioni (sviluppo/debug) |
| job_bronze_transactions.py | Versione job-ready per orchestrazione DAB |

## Bronze — note tecniche
- Tutto StringType in Bronze, nessun cast logico
- date nelle transazioni: YYMMDD come stringa grezza → parsing in Silver
- Auto Loader: schema esplicito (no inferSchema), no cloudFiles.schemaLocation
- partitionBy year/month → spostato in Silver (parsing date fatto lì)
- Checkpoint: abfss://raw@czechfintechdata.dfs.core.windows.net/checkpoints/bronze_transactions

## Prossimi step
1. Silver: join transactions ↔ account ↔ client ↔ district
2. Silver: cast tipi (date → DateType, amount → Decimal, ecc.)
3. Silver: SCD Type 2 su account (frequency può cambiare)
4. Gold: loan_risk_summary, account_kpi, transaction_trends
5. DAB: orchestrazione notebook in pipeline
