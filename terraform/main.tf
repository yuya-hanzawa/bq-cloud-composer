provider "google" {
  project = var.PROJECT_ID
  region  = var.REGION
}

resource "google_storage_bucket" "Create_GCS_For_Data_Lake" {
  name     = var.BUCKET
  storage_class = "REGIONAL"
  location = var.REGION
}

resource "google_bigquery_dataset" "Create_Lake_Table" {
  dataset_id  = var.LAKE_DATASET_ID
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
        project_id        = var.PROJECT_ID
        bucket            = var.BUCKET
        server_port       = var.SERVER_PORT
        username          = var.USERNAME
        password          = var.PASSWORD
        source_dataset_id = var.LAKE_DATASET_ID
        dwh_dataset_id    = var.DWH_DATASET_ID
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
