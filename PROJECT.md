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
    └── transactions/ ← trans_0.csv ... trans_105.csv (drop incrementale)

Databricks: adb-7405607744677493.13.azuredatabricks.net
└── czech_fintech (catalog)
    ├── bronze  → ingestion raw as-is
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
- [x] Catalog czech_fintech + schema bronze creati (Setup.py)
- [x] Test read_files() su card.csv → OK
- [ ] Bronze: batch statici (account, client, card, disp, district, loan, order)
- [ ] Bronze: Auto Loader trans (trans_0.csv ... trans_105.csv)
- [ ] Silver: join, cast, SCD Type 2
- [ ] Gold: loan_risk_summary, account_kpi, transaction_trends
- [ ] DAB orchestrazione

1. Bronze batch statici     ← adesso
2. Bronze Auto Loader trans ← dopo, con gli altri CSV caricati
3. Silver joins + typing    ← dipende da 1 e 2
4. Gold aggregations        ← dipende da 3
5. DAB orchestrazione       ← alla fine, tutto insieme

## Cluster
- Personal Compute (Single User), single node
- Usato solo per ingestion/sviluppo notebook
- Auto-terminate configurato

## Prossimi step
1. Aggiornare storage.tf: sostituire SP con Access Connector (managed identity)
2. Aggiornare unity_catalog.tf: aggiungere storage credential + external location via Terraform
3. Bronze batch notebook: ingestione 7 file statici come Delta table
4. Bronze Auto Loader notebook: ingestione incrementale trans_*.csv
5. Silver + Gold + DAB





databricks_workspace_url = "adb-7405607744677493.13.azuredatabricks.net"
raw_container_abfss_path = "abfss://raw@czechfintechdata.dfs.core.windows.net/"
service_principal_client_id = "05fa7e2d-9c9a-4779-b0d2-e6f1fd18d886"
storage_account_name = "czechfintechdata"
storage_account_primary_dfs_endpoint = "https://czechfintechdata.dfs.core.windows.net/"
unity_catalog_name = "czech_fintech"
 databricks unity-catalog catalogs list



 
databricks unity-catalog schemas list --catalog-name czech_fintech {
  "catalogs": [
    {
      "name": "czech_fintech",
      "owner": "lorenzo.iulianokk@gmail.com",
      "comment": "Catalog principale progetto Czech Financial Dataset",
      "storage_root": "abfss://raw@czechfintechdata.dfs.core.windows.net/unity-catalog",
      "enable_auto_maintenance": "INHERIT",
      "enable_predictive_optimization": "INHERIT",
      "catalog_type": "MANAGED_CATALOG",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "created_at": 1775134690605,
      "created_by": "lorenzo.iulianokk@gmail.com",
      "updated_at": 1775134690605,
      "updated_by": "lorenzo.iulianokk@gmail.com",
      "storage_location": "abfss://raw@czechfintechdata.dfs.core.windows.net/unity-catalog/__unitystorage/catalogs/5e0af3a4-c87a-42b6-8642-b82b8915bc5e",
      "isolation_mode": "OPEN",
      "accessible_in_current_workspace": true,
      "effective_auto_maintenance_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "effective_predictive_optimization_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "browse_only": false,
      "id": "5e0af3a4-c87a-42b6-8642-b82b8915bc5e",
      "full_name": "czech_fintech",
      "securable_type": "CATALOG",
      "securable_kind": "CATALOG_STANDARD",
      "resource_name": "/metastores/d8bed9d6-a3e6-45f6-8b0a-6304295ca361/catalogs/5e0af3a4-c87a-42b6-8642-b82b8915bc5e",
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1ORc0t"
    },
    {
      "name": "databricks_czech_fintech",
      "owner": "_workspace_admins_databricks_czech_fintech_7405607744677493",
      "storage_root": "abfss://unity-catalog-storage@dbstorage7rd45tfsb33gi.dfs.core.windows.net/7405607744677493",
      "enable_auto_maintenance": "INHERIT",
      "enable_predictive_optimization": "INHERIT",
      "catalog_type": "MANAGED_CATALOG",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "created_at": 1775045214759,
      "created_by": "lorenzo.iulianokk@gmail.com",
      "updated_at": 1775045217569,
      "updated_by": "lorenzo.iulianokk@gmail.com",
      "storage_location": "abfss://unity-catalog-storage@dbstorage7rd45tfsb33gi.dfs.core.windows.net/7405607744677493/__unitystorage/catalogs/9956f306-2612-4d2b-a0df-10023290f799",
      "isolation_mode": "ISOLATED",
      "accessible_in_current_workspace": true,
      "effective_auto_maintenance_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "effective_predictive_optimization_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "browse_only": false,
      "id": "9956f306-2612-4d2b-a0df-10023290f799",
      "full_name": "databricks_czech_fintech",
      "securable_type": "CATALOG",
      "securable_kind": "CATALOG_STANDARD",
      "resource_name": "/metastores/d8bed9d6-a3e6-45f6-8b0a-6304295ca361/catalogs/9956f306-2612-4d2b-a0df-10023290f799",
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1I8I0h"
    },
    {
      "name": "samples",
      "owner": "System user",
      "comment": "These sample datasets are made available by third party data providers as well as open data sources. You can learn more about each data set by clicking on each one.\n\nTo discover more instantly available, free data sets across a wide range of industry use cases, visit [Databricks Marketplace](/marketplace).\n\nPlease note that the third party data sets represent a reduced portion of the available data attributes, volume, and data types available from providers, and are intended for educational rather than production purposes.",
      "catalog_type": "SYSTEM_CATALOG",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "created_at": 1775045208813,
      "created_by": "System user",
      "updated_at": 1775073966724,
      "updated_by": "System user",
      "isolation_mode": "OPEN",
      "accessible_in_current_workspace": true,
      "browse_only": false,
      "provisioning_info": {
        "state": "ACTIVE"
      },
      "id": "481b95da-e3f6-4641-ac11-431acc0504fb",
      "full_name": "samples",
      "securable_type": "CATALOG",
      "securable_kind": "CATALOG_SYSTEM",
      "resource_name": "/metastores/d8bed9d6-a3e6-45f6-8b0a-6304295ca361/catalogs/481b95da-e3f6-4641-ac11-431acc0504fb",
      "delta_sharing_valid_through_timestamp": 1775074026631,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1KpzqE"
    },
    {
      "name": "system",
      "owner": "System user",
      "comment": "System catalog (auto-created)",
      "catalog_type": "SYSTEM_CATALOG",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "created_at": 1775045207629,
      "created_by": "System user",
      "updated_at": 1775045453853,
      "updated_by": "System user",
      "isolation_mode": "OPEN",
      "accessible_in_current_workspace": true,
      "browse_only": false,
      "provisioning_info": {
        "state": "ACTIVE"
      },
      "id": "64b6c1ed-f9b2-4173-8a68-4a585520e938",
      "full_name": "system",
      "securable_type": "CATALOG",
      "securable_kind": "CATALOG_SYSTEM",
      "resource_name": "/metastores/d8bed9d6-a3e6-45f6-8b0a-6304295ca361/catalogs/64b6c1ed-f9b2-4173-8a68-4a585520e938",
      "delta_sharing_valid_through_timestamp": 1775045513773,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1I9Cgd"
    }
  ]
}
{
  "schemas": [
    {
      "name": "bronze",
      "catalog_name": "czech_fintech",
      "owner": "lorenzo.iulianokk@gmail.com",
      "comment": "Raw ingestion layer - dati grezzi as-is",
      "enable_auto_maintenance": "INHERIT",
      "enable_predictive_optimization": "INHERIT",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "full_name": "czech_fintech.bronze",
      "created_at": 1775134696822,
      "created_by": "lorenzo.iulianokk@gmail.com",
      "updated_at": 1775134696822,
      "updated_by": "lorenzo.iulianokk@gmail.com",
      "catalog_type": "MANAGED_CATALOG",
      "effective_auto_maintenance_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "effective_predictive_optimization_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "schema_id": "17dc3f9f-4da4-4880-a0df-27830145efe7",
      "securable_type": "SCHEMA",
      "securable_kind": "SCHEMA_STANDARD",
      "browse_only": false,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1OReV2"
    },
    {
      "name": "gold",
      "catalog_name": "czech_fintech",
      "owner": "lorenzo.iulianokk@gmail.com",
      "comment": "Aggregation layer - loan_risk_summary, account_kpi, transaction_trends",
      "enable_auto_maintenance": "INHERIT",
      "enable_predictive_optimization": "INHERIT",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "full_name": "czech_fintech.gold",
      "created_at": 1775134696651,
      "created_by": "lorenzo.iulianokk@gmail.com",
      "updated_at": 1775134696651,
      "updated_by": "lorenzo.iulianokk@gmail.com",
      "catalog_type": "MANAGED_CATALOG",
      "effective_auto_maintenance_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "effective_predictive_optimization_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "schema_id": "e5c63e1d-4dba-4211-bd5d-aba7e3e903f4",
      "securable_type": "SCHEMA",
      "securable_kind": "SCHEMA_STANDARD",
      "browse_only": false,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1OReTL"
    },
    {
      "name": "information_schema",
      "catalog_name": "czech_fintech",
      "owner": "System user",
      "comment": "Information schema (auto-created)",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "full_name": "czech_fintech.information_schema",
      "created_at": 1775134690635,
      "created_by": "System user",
      "updated_at": 1775134690635,
      "updated_by": "System user",
      "catalog_type": "MANAGED_CATALOG",
      "schema_id": "14b5988c-309c-44a3-b5af-c2054dab98e5",
      "securable_type": "SCHEMA",
      "securable_kind": "SCHEMA_SYSTEM",
      "browse_only": false,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1ORc1L"
    },
    {
      "name": "silver",
      "catalog_name": "czech_fintech",
      "owner": "lorenzo.iulianokk@gmail.com",
      "comment": "Cleaned layer - join, typing, SCD Type 2",
      "enable_auto_maintenance": "INHERIT",
      "enable_predictive_optimization": "INHERIT",
      "metastore_id": "d8bed9d6-a3e6-45f6-8b0a-6304295ca361",
      "full_name": "czech_fintech.silver",
      "created_at": 1775134696935,
      "created_by": "lorenzo.iulianokk@gmail.com",
      "updated_at": 1775134696935,
      "updated_by": "lorenzo.iulianokk@gmail.com",
      "catalog_type": "MANAGED_CATALOG",
      "effective_auto_maintenance_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "effective_predictive_optimization_flag": {
        "value": "ENABLE",
        "inherited_from_type": "METASTORE",
        "inherited_from_name": "metastore_azure_eastus"
      },
      "schema_id": "d48065c6-4850-4372-9608-364b55aa8403",
      "securable_type": "SCHEMA",
      "securable_kind": "SCHEMA_STANDARD",
      "browse_only": false,
      "metastore_version": -1,
      "cache_version_info": {
        "metastore_version": -1
      },
      "etag": "CAESCAAAAZ1OReXn"
    }
  ]
}
