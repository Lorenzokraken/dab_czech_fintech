output "databricks_workspace_url" {
  description = "URL del workspace Databricks"
  value       = data.azurerm_databricks_workspace.main.workspace_url
}

output "storage_account_name" {
  description = "Nome dello storage account dati"
  value       = azurerm_storage_account.data.name
}

output "storage_account_primary_dfs_endpoint" {
  description = "Endpoint ADLS Gen2 (dfs)"
  value       = azurerm_storage_account.data.primary_dfs_endpoint
}

output "raw_container_abfss_path" {
  description = "Path abfss del container raw (usato in Databricks)"
  value       = "abfss://raw@${azurerm_storage_account.data.name}.dfs.core.windows.net/"
}

output "service_principal_client_id" {
  description = "Client ID del Service Principal"
  value       = azuread_application.databricks_sp.client_id
}

output "unity_catalog_name" {
  description = "Nome del catalog Unity Catalog (creato manualmente via SQL nel workspace)"
  value       = "czech_fintech"
}
