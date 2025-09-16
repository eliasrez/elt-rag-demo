terraform {
  required_version = ">= 1.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "59d84c08-1029-4c6a-abcd-c61a5dee4d25"
}

# --------------- Resource Group ---------------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# --------------- Storage Account ---------------
resource "azurerm_storage_account" "sa" {
  name                     = lower(var.storage_account_name)
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  #allow_blob_public_access = false
}

resource "azurerm_storage_container" "rawfiles" {
  name                  = var.blob_container_name
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

# --------------- Key Vault (for secrets) ---------------
resource "azurerm_key_vault" "kv" {
  name                        = var.key_vault_name
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  #soft_delete_enabled         = true
  purge_protection_enabled    = false

  network_acls {
    default_action             = "Allow"
    bypass                     = "AzureServices"
  }
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "openai-api-key"
  value        = var.openai_api_key
  key_vault_id = azurerm_key_vault.kv.id
}

# --------------- Cognitive Search ---------------
# Note: SKU can be 'basic' for evaluation. Increase to 'standard' or higher for production.
resource "azurerm_search_service" "search" {
  name                = var.search_service_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = var.search_sku
  partition_count     = var.search_partition_count
  replica_count       = var.search_replica_count

  # optional identity if you want managed identity access from other services
  identity {
    type = "SystemAssigned"
  }
}

# --------------- Optional: Managed Identity Role Assignment (to access storage) ---------------
# Give the search service (or other system-assigned identity) blob data reader access to the storage
resource "azurerm_role_assignment" "search_blob_reader" {
  scope                = azurerm_storage_account.sa.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.search.identity[0].principal_id
  depends_on           = [azurerm_search_service.search]
}

# --------------- Data sources ---------------
data "azurerm_client_config" "current" {}


# --- Azure Container Registry (ACR) ---
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
}

# --- Optionally create a service principal to push images (CI use) ---
resource "azuread_application" "acr_push_app" {
  display_name = "${var.acr_name}-push-app"
}

resource "azuread_service_principal" "acr_push_sp" {
  client_id = azuread_application.acr_push_app.application_id
}

resource "azuread_service_principal_password" "acr_push_sp_pwd" {
  service_principal_id = azuread_service_principal.acr_push_sp.id
  value                 = random_password.acr_sp_password.result
  end_date              = timeadd(timestamp(), "240h")
}

resource "random_password" "acr_sp_password" {
  length  = 24
  special = true
}

# Grant the SP acr push role on the registry
resource "azurerm_role_assignment" "acr_push" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPush"
  principal_id         = azuread_service_principal.acr_push_sp.object_id
}

# --- Optionally create a system-assigned identity for ACI usage (if desired) ---
# We'll let ACI pull images from ACR using a managed identity later; ACI does not support system-assigned identity in TF yet directly for all versions,
# so we'll keep the simple flow (use admin-enabled ACR credentials or a managed identity / service principal).
#
# --- Outputs ---
output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}

output "acr_push_sp_app_id" {
  value = azuread_application.acr_push_app.application_id
}

output "acr_push_sp_password" {
  value     = random_password.acr_sp_password.result
  sensitive = true
}



