variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
  default     = "rag-demo-rg"
}

variable "storage_account_name" {
  type        = string
  description = "Storage account name (must be globally unique, lowercase)"
  default     = "ragtfstorageacct001"
}

variable "blob_container_name" {
  type        = string
  description = "Blob container to hold raw files"
  default     = "rawfiles"
}

variable "key_vault_name" {
  type        = string
  description = "Key Vault name (must be globally unique)"
  default     = "ragdemo-kv-001"
}

variable "openai_api_key" {
  type        = string
  description = "Optional: place OpenAI API key here for initial secret creation (or set later)"
  default     = ""
  sensitive   = true
}

variable "search_service_name" {
  type        = string
  description = "Azure Cognitive Search service name (must be globally unique)"
  default     = "rag-demo-search-svc"
}

variable "search_sku" {
  type        = string
  description = "SKU for Azure Cognitive Search (basic, standard, etc.)"
  default     = "basic"
}

variable "search_partition_count" {
  type        = number
  default     = 1
}

variable "search_replica_count" {
  type        = number
  default     = 1
}

variable "acr_name" {
  description = "ACR name (must be globally unique, lowercase)"
  type        = string
  default     = "ragtfacr001"
}