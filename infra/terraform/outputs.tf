output "resource_group_name" {
  description = "Resource group owned by this temporary environment."
  value       = azurerm_resource_group.wordle.name
}

output "cluster_name" {
  description = "AKS name for a future explicit get-credentials operation."
  value       = azurerm_kubernetes_cluster.wordle.name
}

output "cluster_id" {
  description = "AKS ARM resource identifier, not a credential."
  value       = azurerm_kubernetes_cluster.wordle.id
}

output "node_resource_group_name" {
  description = "AKS-managed group containing billable node resources."
  value       = azurerm_kubernetes_cluster.wordle.node_resource_group
}

output "subnet_id" {
  description = "Subnet assigned to AKS nodes."
  value       = azurerm_subnet.aks.id
}

output "control_plane_identity_principal_id" {
  description = "Managed identity principal, not a credential."
  value       = azurerm_user_assigned_identity.aks.principal_id
}
