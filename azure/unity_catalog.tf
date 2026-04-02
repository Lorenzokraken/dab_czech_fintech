# Legge l'Access Connector esistente (creato manualmente)
data "azurerm_databricks_access_connector" "main" {
  name                = "ac-czech-fintech-databricks"
  resource_group_name = var.resource_group_name
}

# Assegna al Managed Identity dell'Access Connector il ruolo sullo storage
resource "azurerm_role_assignment" "connector_storage_contributor" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_databricks_access_connector.main.identity[0].principal_id
}

# Storage Credential in Unity Catalog
# Usa Managed Identity dell'Access Connector (evita problemi di permessi admin)
resource "databricks_storage_credential" "adls" {
  name = "czechfintech-sc"

  azure_managed_identity {
    access_connector_id = data.azurerm_databricks_access_connector.main.id
  }

  comment = "Storage credential per ADLS Gen2 czech-fintech-data"
}

# External Location: punta al container raw/ su ADLS Gen2
resource "databricks_external_location" "raw" {
  name            = "czechfintech-raw"
  url             = "abfss://raw@${azurerm_storage_account.data.name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.adls.name
  comment         = "External location per i dati raw del progetto czech-fintech"
}

# Catalog Unity Catalog per il progetto
resource "databricks_catalog" "czech_fintech" {
  name          = "czech_fintech"
  comment       = "Catalog principale progetto Czech Financial Dataset"
  storage_root  = "abfss://raw@${azurerm_storage_account.data.name}.dfs.core.windows.net/unity-catalog/"
  force_destroy = true
}

# Schema Bronze
resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.czech_fintech.name
  name         = "bronze"
  comment      = "Raw ingestion layer - dati grezzi as-is"
}

# Schema Silver
resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.czech_fintech.name
  name         = "silver"
  comment      = "Cleaned layer - join, typing, SCD Type 2"
}

# Schema Gold
resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.czech_fintech.name
  name         = "gold"
  comment      = "Aggregation layer - loan_risk_summary, account_kpi, transaction_trends"
}
