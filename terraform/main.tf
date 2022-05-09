provider "google" {
  project = var.PROJECT
  region  = var.REGION
}

resource "google_bigquery_dataset" "Create_Source_Table" {
  dataset_id  = var.SOURCE_DATASET_ID
  description = "アクセスログの外部テーブル"
  location    = "US"
}

resource "google_bigquery_dataset" "Create_DWH_Table" {
  dataset_id  = var.DWH_DATASET_ID
  description = "自作のホームページのアクセスログを集計するデータウェアハウス"
  location    = "US"
}

resource "google_composer_environment" "Create_Cloud_Composer" {
  name   = "hp-access-log-composer"
  region = var.REGION

  config {
    software_config {
      image_version = "composer-2.0.11-airflow-2.2.3"

      pypi_packages = {
        scp = "==0.14.1"
        }

      env_variables = {
        PROJECT           = var.PROJECT
        BUCKET            = var.BUCKET
        SERVER_PORT       = var.SERVER_PORT
        USERNAME          = var.USERNAME
        PASSWORD          = var.PASSWORD
        SOURCE_DATASET_ID = var.SOURCE_DATASET_ID
        DWH_DATASET_ID    = var.DWH_DATASET_ID
        }
    }

    workloads_config {
      scheduler {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        count      = 1
      }
      web_server {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
      }
      worker {
        cpu = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        min_count  = 1
        max_count  = 3
      }
    }

    node_config {
      service_account = var.SERVICE_ACCOUNT
    }
  }
}
