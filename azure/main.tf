terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.40"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }
  }
  required_version = ">= 1.5"
}

provider "azurerm" {
  subscription_id               = var.subscription_id
  resource_provider_registrations = "none"
  features {}
}

# Provider Databricks punta al workspace già esistente
provider "databricks" {
  host                        = "https://${data.azurerm_databricks_workspace.main.workspace_url}"
  azure_workspace_resource_id = data.azurerm_databricks_workspace.main.id
  auth_type                   = "azure-cli"
}

# Legge il workspace Databricks esistente (creato manualmente)
data "azurerm_databricks_workspace" "main" {
  name                = var.databricks_workspace_name
  resource_group_name = var.resource_group_name
}

# Legge il resource group esistente
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}
