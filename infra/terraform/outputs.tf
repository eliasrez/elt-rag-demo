output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "storage_account_name" {
  value = azurerm_storage_account.sa.name
}

output "storage_container_name" {
  value = azurerm_storage_container.rawfiles.name
}

output "key_vault_id" {
  value = azurerm_key_vault.kv.id
}

output "cognitive_search_service_name" {
  value = azurerm_search_service.search.name
}

output "cognitive_search_endpoint_hint" {
  value = "https://${azurerm_search_service.search.name}.search.windows.net (use portal or az cli to get admin keys)"
}

