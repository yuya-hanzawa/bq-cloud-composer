provider "google" {
  project = var.PROJECT_ID
  region  = var.REGION
}

module "gcp_services" {
  source = "./modules/"
  BUCKET              = var.BUCKET
  REGION              = var.REGION
  EXTERNAL_DATASET_ID = var.EXTERNAL_DATASET_ID
  DWH_DATASET_ID      = var.DWH_DATASET_ID
  PROJECT_ID          = var.PROJECT_ID
  SERVER_PORT         = var.SERVER_PORT
  USERNAME            = var.USERNAME
  ROOT_PASSWORD       = var.ROOT_PASSWORD
  SSH_PASSWORD        = var.SSH_PASSWORD
  SERVICE_ACCOUNT     = var.SERVICE_ACCOUNT
}