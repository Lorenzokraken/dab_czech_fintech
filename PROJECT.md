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
- [ ] Sicurezza repo e teardown risorse Azure

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
- partitionBy year/month → spostato in Silver dove si fa il parsing della data
- Checkpoint: abfss://raw@czechfintechdata.dfs.core.windows.net/checkpoints/bronze_transactions

## Prossimi step dettagliati

### 1. Silver — join e typing
La tabella centrale è `transactions`, che va arricchita con le dimensioni.
Il join principale è: `transactions → account → client → district` (tramite disp come bridge).
In Silver si fanno tutti i cast che in Bronze erano stati evitati:
- `date` (YYMMDD stringa) → `DateType` con `to_date(concat("19", date), "yyyyMMdd")`
- `amount`, `balance`, `payments` → `DecimalType(15,2)`
- `duration` → `IntegerType`
- `birth_number` → decodifica sesso e data di nascita (YYMM+50DD per donne)
Qui si aggiunge anche il partizionamento `year/month` sulle transazioni,
che in Bronze era stato rimandato per evitare il parsing della data.

### 2. Silver — SCD Type 2 su account
`account.frequency` (frequenza estratto conto) può cambiare nel tempo.
Va gestita con SCD Type 2: ogni cambio genera una nuova riga con
`valid_from`, `valid_to`, `is_current`. Si usa `MERGE INTO` Delta
con la logica di confronto sul valore corrente vs arrivo.
È il pattern più complesso del progetto e il più rilevante per il portfolio.

### 3. Gold — aggregazioni per analytics
Tre tabelle finali, ognuna risponde a una domanda di business:
- `loan_risk_summary`: per ogni prestito, stato (A/B/C/D), importo, durata,
  rata mensile, e profilo del cliente (distretto, età). Serve per risk scoring.
- `account_kpi`: per ogni conto, volume totale transazioni in/out,
  saldo medio, numero operazioni per mese. Serve per segmentazione clienti.
- `transaction_trends`: aggregazione mensile per distretto — volume medio,
  tipologia operazioni prevalente (PRIJEM/VYDAJ). Serve per trend geografici.
Tutte le Gold sono tabelle statiche overwrite (no streaming), leggere e pronte
per essere consumate da un tool BI o da una dashboard.

### 4. DAB — orchestrazione
Databricks Asset Bundle definisce la pipeline come codice versionabile.
Il bundle conterrà:
- Un job con task in sequenza: schema → bronze_static → bronze_transactions → silver → gold
- Parametri di ambiente (dev/prod) gestiti via variabili DAB
- Il notebook `job_bronze_transactions` come task dedicato per le transazioni
  (unico che gira incrementalmente, gli altri sono idempotenti)
La struttura DAB va in repo e permette di deployare l'intera pipeline
con un singolo `databricks bundle deploy`.

## ⚠️ SICUREZZA REPO E TEARDOWN — DA FARE PRIMA DI PUBBLICARE

### Cosa è sicuro lasciare pubblico
I nomi delle risorse Azure (`czechfintechdata`, `li-rg`, `adb-7405607744677493.13`)
non sono credenziali — sono identificatori pubblici. Lasciarli nel README
dà credibilità al progetto: si vede che è infrastruttura reale su Azure, non mockata.

### Cosa NON deve mai andare in repo
- `terraform.tfvars` → contiene subscription_id, tenant_id → già in .gitignore, verificare
- Client Secret del Service Principal → non deve comparire in nessun file
- Eventuali token o API key nei notebook → verificare tutte le celle

### Checklist sicurezza prima del push pubblico
- [ ] Verificare `.gitignore` copre: `*.tfvars`, `*.tfstate`, `*.tfstate.backup`, `.terraform/`
- [ ] Grep nel repo per `subscription_id`, `tenant_id`, `client_secret` → devono essere vuoti
- [ ] Nei notebook: nessuna variabile hardcoded con valori sensibili
- [ ] Aggiungere nel README sezione "Replicate this project" con placeholder:
      STORAGE_ACCOUNT=czechfintechdata     # → sostituisci col tuo
      DATABRICKS_HOST=adb-7405607...       # → sostituisci col tuo
      RESOURCE_GROUP=li-rg                 # → sostituisci col tuo

### Teardown risorse Azure
Quando il progetto è completo e documentato, eliminare tutte le risorse
per evitare consumo di credito sulla trial Azure.
Terraform rende il teardown immediato:
```
cd azure/
terraform destroy
```
Questo elimina: Storage Account, Service Principal, role assignments.
Il workspace Databricks e il Resource Group vanno eliminati manualmente
da portale Azure (o aggiunti a Terraform prima del destroy).

Tenere in locale prima del destroy:
- Tutti i notebook (già in repo)
- Screenshot della UI Databricks con le tabelle e il catalog
- Output della cella di verifica Bronze (row counts)
- PROJECT.md aggiornato con architettura finale
