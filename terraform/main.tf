provider "google" {
  project     = var.PROJECT_ID
  region      = var.REGION
}

resource "google_bigquery_dataset" "source_table" {
  dataset_id                  = var.SOURCE_DATASET_ID
  description                 = "アクセスログの外部テーブル"
  location                    = "US"
}

resource "google_bigquery_dataset" "DWH_table" {
  dataset_id                  = var.DWH_DATASET_ID
  description                 = "自作のホームページのアクセスログを集計するデータウェアハウス"
  location                    = "US"
}

resource "google_composer_environment" "HP_access_log" {
  name   = "HP_access_log"
  region = var.REGION

  config {
    
    software_config {
      scheduler_count = 2
      image_version = "composer-2.0.11-airflow-2.2.3"
      python_version = "3"

      pypi_packages = {
        scp = "==0.14.1"
        }

      env_variables = {
        PROJECT_ID = var.PROJECT_ID
        BUCKET = var.BUCKET
        PORT = var.PORT
        USERNAME = var.USERNAME
        PASSWORD = var.PASSWORD
        SOURCE_DATASET_ID = var.SOURCE_DATASET_ID
        DWH_DATASET_ID = var.DWH_DATASET_ID
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
