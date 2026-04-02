variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "Nome del resource group esistente"
  type        = string
  default     = "li-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "databricks_workspace_name" {
  description = "Nome del workspace Databricks esistente"
  type        = string
  default     = "databricks-czech-fintech"
}

variable "storage_account_name" {
  description = "Nome dello storage account dati raw (deve essere unico globalmente)"
  type        = string
  default     = "czechfintechdata"
}

variable "databricks_account_id" {
  description = "Databricks Account ID (trovalo su accounts.azuredatabricks.net)"
  type        = string
  sensitive   = true
}
