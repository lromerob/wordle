locals {
  tags = merge(var.tags, {
    project    = "wordle"
    managed_by = "terraform"
  })
}

resource "azurerm_resource_group" "wordle" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "wordle" {
  name                = var.vnet_name
  location            = azurerm_resource_group.wordle.location
  resource_group_name = azurerm_resource_group.wordle.name
  address_space       = ["10.10.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "aks" {
  name                 = var.subnet_name
  resource_group_name  = azurerm_resource_group.wordle.name
  virtual_network_name = azurerm_virtual_network.wordle.name
  address_prefixes     = ["10.10.0.0/24"]
}

resource "azurerm_user_assigned_identity" "aks" {
  name                = var.identity_name
  location            = azurerm_resource_group.wordle.location
  resource_group_name = azurerm_resource_group.wordle.name
  tags                = local.tags
}

# Grant only subnet networking permissions before creating the AKS control plane.
resource "azurerm_role_assignment" "aks_network" {
  scope                            = azurerm_subnet.aks.id
  role_definition_name             = "Network Contributor"
  principal_id                     = azurerm_user_assigned_identity.aks.principal_id
  skip_service_principal_aad_check = true
}

resource "azurerm_kubernetes_cluster" "wordle" {
  name                              = var.cluster_name
  location                          = azurerm_resource_group.wordle.location
  resource_group_name               = azurerm_resource_group.wordle.name
  node_resource_group               = var.node_resource_group_name
  dns_prefix                        = var.dns_prefix
  kubernetes_version                = var.kubernetes_version
  sku_tier                          = "Free"
  role_based_access_control_enabled = true
  local_account_disabled            = true
  private_cluster_enabled           = false
  tags                              = local.tags

  default_node_pool {
    name            = var.node_pool_name
    vm_size         = var.node_vm_size
    node_count      = var.node_count
    vnet_subnet_id  = azurerm_subnet.aks.id
    max_pods        = 30
    os_disk_type    = "Managed"
    os_disk_size_gb = var.os_disk_size_gb
    os_sku          = "Ubuntu"
    type            = "VirtualMachineScaleSets"
    tags            = local.tags
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  azure_active_directory_role_based_access_control {
    tenant_id              = var.tenant_id
    admin_group_object_ids = var.admin_group_object_ids
    azure_rbac_enabled     = false
  }

  api_server_access_profile {
    authorized_ip_ranges = var.api_authorized_cidrs
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    pod_cidr            = "10.244.0.0/16"
    service_cidr        = "10.20.0.0/16"
    dns_service_ip      = "10.20.0.10"
    load_balancer_sku   = "standard"
    outbound_type       = "loadBalancer"

    load_balancer_profile {
      managed_outbound_ip_count = 1
    }
  }

  # No ACR, Supabase, observability add-ons or workload resources.
  depends_on = [azurerm_role_assignment.aks_network]
}
