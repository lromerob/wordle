terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.50.0"
    }
  }

  # Partial configuration. Storage must already exist; this module never creates it.
  backend "azurerm" {
    use_azuread_auth = true
  }
}
