# Storage Account dedicato ai dati raw (separato da quello managed di Databricks)
resource "azurerm_storage_account" "data" {
  name                     = var.storage_account_name
  resource_group_name      = data.azurerm_resource_group.main.name
  location                 = data.azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Abilita ADLS Gen2 (hierarchical namespace)
  is_hns_enabled = true

  tags = {
    project     = "czech-fintech"
    environment = "dev"
    managed_by  = "terraform"
  }
}

# Container "raw" per i dati grezzi
resource "azurerm_storage_container" "raw" {
  name                   = "raw"
  storage_account_id     = azurerm_storage_account.data.id
  container_access_type  = "private"
}

# Service Principal per Databricks → accesso allo storage
resource "azuread_application" "databricks_sp" {
  display_name = "sp-czech-fintech-databricks"
}

resource "azuread_service_principal" "databricks_sp" {
  client_id = azuread_application.databricks_sp.client_id
}

resource "azuread_service_principal_password" "databricks_sp" {
  service_principal_id = azuread_service_principal.databricks_sp.id
}
# Assegna al Service Principal il ruolo "Storage Blob Data Contributor"
# sullo storage account dei dati raw
resource "azurerm_role_assignment" "sp_storage_contributor" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.databricks_sp.object_id
}

# Legge il tenant corrente (serve per Unity Catalog)
data "azurerm_client_config" "current" {}
