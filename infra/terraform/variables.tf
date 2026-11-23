variable "subscription_id" {
  description = "Target subscription UUID; supplied explicitly, never inferred."
  type        = string
}

variable "tenant_id" {
  description = "Microsoft Entra tenant UUID for operator and cluster identities."
  type        = string
}

variable "location" {
  description = "Azure region; verify AKS support, SKU availability and costs first."
  type        = string
  default     = "swedencentral"
}

variable "resource_group_name" {
  description = "Dedicated resource group; must not contain unrelated resources."
  type        = string
  default     = "rg-wordle-academic"
}

variable "node_resource_group_name" {
  description = "New group created and managed by AKS for node resources."
  type        = string
  default     = "rg-wordle-academic-nodes"
}

variable "cluster_name" {
  description = "Temporary AKS cluster name."
  type        = string
  default     = "aks-wordle-academic"
}

variable "dns_prefix" {
  description = "AKS public API DNS prefix."
  type        = string
  default     = "wordle-academic"
}

variable "vnet_name" {
  description = "Dedicated virtual network name."
  type        = string
  default     = "vnet-wordle-academic"
}

variable "subnet_name" {
  description = "AKS node subnet name."
  type        = string
  default     = "snet-aks"
}

variable "identity_name" {
  description = "User-assigned control plane identity name."
  type        = string
  default     = "id-wordle-aks"
}

variable "node_pool_name" {
  description = "Linux system pool name, 1-12 lowercase alphanumeric characters."
  type        = string
  default     = "system"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{0,11}$", var.node_pool_name))
    error_message = "Use 1-12 lowercase alphanumeric characters, beginning with a letter."
  }
}

variable "node_vm_size" {
  description = "System pool SKU; verify >=4 vCPUs, >=4 GB, regional support and quota. No B-series."
  type        = string
  default     = "Standard_D4s_v5"

  validation {
    condition     = !can(regex("(?i)^Standard_B", var.node_vm_size))
    error_message = "B-series is not supported for an AKS system pool."
  }
}

variable "node_count" {
  description = "System pool nodes. Academic minimum follows current AKS guidance; not HA sizing."
  type        = number
  default     = 2

  validation {
    condition     = var.node_count >= 2 && var.node_count == floor(var.node_count)
    error_message = "Use an integer of at least two nodes; increasing it increases cost."
  }
}

variable "os_disk_size_gb" {
  description = "Managed OS disk capacity per node in GB; billed separately from compute."
  type        = number
  default     = 64

  validation {
    condition     = var.os_disk_size_gb >= 30 && var.os_disk_size_gb == floor(var.os_disk_size_gb)
    error_message = "Use an integer disk capacity of at least 30 GB."
  }
}

variable "kubernetes_version" {
  description = "Approved Sweden Central Kubernetes patch; revalidate regional support before provisioning."
  type        = string
  default     = "1.35.9"
  nullable    = false
}

variable "admin_group_object_ids" {
  description = "Existing Entra security groups granted Kubernetes cluster-admin; object IDs, not secrets."
  type        = list(string)

  validation {
    condition     = length(var.admin_group_object_ids) > 0
    error_message = "Supply at least one existing administrator group to avoid lockout."
  }
}

variable "api_authorized_cidrs" {
  description = "Explicitly approved administrative public IPv4 /32 addresses; no implicit default."
  type        = list(string)
  nullable    = false

  validation {
    condition = length(var.api_authorized_cidrs) == 1 && alltrue([
      for cidr in var.api_authorized_cidrs : try(
        can(cidrnetmask(cidr)) && endswith(cidr, "/32") &&
        !can(regex("^(0[.]|10[.]|100[.](6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])[.]|127[.]|169[.]254[.]|172[.](1[6-9]|2[0-9]|3[01])[.]|192[.](0[.]0[.]|0[.]2[.]|88[.]99[.]|168[.])|198[.](1[89][.]|51[.]100[.])|203[.]0[.]113[.]|(22[4-9]|23[0-9]|24[0-9]|25[0-5])[.])", cidr)),
        false
      )
    ])
    error_message = "Supply exactly one approved public IPv4 /32; empty lists, placeholders, private/reserved ranges and broader networks are rejected."
  }
}

variable "api_access_approved" {
  description = "Set true only after the owner explicitly approves every API /32; not an Azure deployment authorization."
  type        = bool
  nullable    = false

  validation {
    condition     = var.api_access_approved
    error_message = "API /32 approval is pending. Obtain explicit owner approval before setting api_access_approved=true."
  }
}

variable "tags" {
  description = "Non-sensitive ownership, environment and lifecycle tags; no credentials or personal data."
  type        = map(string)
  default = {
    environment = "academic"
    lifecycle   = "temporary"
  }
}
