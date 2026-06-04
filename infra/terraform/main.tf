terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }
  backend "azurerm" {
    resource_group_name  = "upv-tfstate-rg"
    storage_account_name = "upvtfstate"
    container_name       = "tfstate"
    key                  = "upv.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "resource_group" {
  type    = string
  default = "upv-rg"
}

# ── AKS Cluster ────────────────────────────────────────────────────────────
resource "azurerm_kubernetes_cluster" "upv" {
  name                = "upv-aks-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group
  dns_prefix          = "upv-${var.environment}"

  default_node_pool {
    name                = "default"
    node_count          = 3
    vm_size             = "Standard_D4s_v3"
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 10
  }

  # AI workload node pool (larger)
  # (add additional node pools via azurerm_kubernetes_cluster_node_pool)

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }

  tags = {
    Environment = var.environment
    Project     = "UPV"
  }
}

# ── Container Registry ──────────────────────────────────────────────────────
resource "azurerm_container_registry" "upv" {
  name                = "upvacr${var.environment}"
  resource_group_name = var.resource_group
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = false
}

# Grant AKS pull access to ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.upv.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.upv.id
  skip_service_principal_aad_check = true
}

# ── Outputs ─────────────────────────────────────────────────────────────────
output "kube_config" {
  value     = azurerm_kubernetes_cluster.upv.kube_config_raw
  sensitive = true
}

output "acr_login_server" {
  value = azurerm_container_registry.upv.login_server
}
