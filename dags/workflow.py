import os
from datetime import datetime, timedelta, timezone
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from google.cloud import bigquery
from google.cloud import storage
from airflow import models
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator

PROJECT_ID      = os.environ['project_id']
LAKE_DATASET_ID = os.environ['lake_dataset_id']
DWH_DATASET_ID  = os.environ['dwh_dataset_id']
BUCKET          = os.environ['bucket']
SERVER_PORT     = os.environ['server_port']
USERNAME        = os.environ['username']
PASSWORD        = os.environ['password']

JST = timezone(timedelta(hours=+9), 'JST')
day = (datetime.now(JST) - timedelta(days=1)).date()
file_name = f'access.log-{day:%Y%m%d}'

def extract_file_from_server_to_gcs():
    with SSHClient() as ssh:
        ssh.set_missing_host_key_policy(AutoAddPolicy())

        ssh.connect(hostname='yuya-hanzawa.com', 
                    port=SERVER_PORT, 
                    username=USERNAME,
                    password=PASSWORD
        )
    
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(f'/var/log/nginx/{file_name}', '/tmp/')

    gcs = storage.Client(PROJECT_ID)
    bucket = gcs.get_bucket(BUCKET)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(f'/tmp/{file_name}')

def load_table_from_gcs_to_bq():
    bq = bigquery.Client(project=PROJECT_ID)
    dataset = bq.dataset(LAKE_DATASET_ID)

    schema=[
        bigquery.SchemaField("time", "STRING", mode='NULLABLE', description='標準フォーマットのローカルタイム'),
        bigquery.SchemaField("remote_host", "STRING", mode='NULLABLE', description='クライアントのIPアドレス'),
        bigquery.SchemaField("host", "STRING", mode='NULLABLE', description='マッチしたサーバ名もしくはHostヘッダ名、なければリクエスト内のホスト'),
        bigquery.SchemaField("user", "STRING", mode='NULLABLE', description='クライアントのユーザー名'),
        bigquery.SchemaField("status", "STRING", mode='NULLABLE', description='レスポンスのHTTPステータスコード'),
        bigquery.SchemaField("protocol", "STRING", mode='NULLABLE', description='リクエストプロトコル'),
        bigquery.SchemaField("method", "STRING", mode='NULLABLE', description='リクエストされたHTTPメソッド'),
        bigquery.SchemaField("path", "STRING", mode='NULLABLE', description='リクエストされたパス'),
        bigquery.SchemaField("size", "STRING", mode='NULLABLE', description='クライアントへの送信バイト数'),
        bigquery.SchemaField("request_time", "STRING", mode='NULLABLE', description='リクエストの処理時間'),
        bigquery.SchemaField("upstream_time", "STRING", mode='NULLABLE', description='サーバーがリクエストの処理にかかった時間'),
        bigquery.SchemaField("user_agent", "STRING", mode='NULLABLE', description='クライアントのブラウザ情報'),
        bigquery.SchemaField("forwardedfor", "STRING", mode='NULLABLE', description='接続元IPアドレス'),
        bigquery.SchemaField("forwardedproto", "STRING", mode='NULLABLE', description='HTTP HTTPS判定'),
        bigquery.SchemaField("referrer", "STRING", mode='NULLABLE', description='Webページの参照元')
    ]

    table = bigquery.Table(dataset.table(f'HP-access-log-{day:%Y%m%d}'), schema=schema)
    external_config = bigquery.ExternalConfig("NEWLINE_DELIMITED_JSON")
    external_config.source_uris = [
      f'gs://{BUCKET}/{file_name}'
    ]
    table.external_data_configuration = external_config
    table = bq.create_table(table)

default_dag_args = {
    'start_date': '2022-05-15',
    'depends_on_past': True,
    'wait_for_downstream': True
}

with models.DAG(
    dag_id = 'HP-access-log',
    schedule_interval = '0 3 * * *',
    default_args = default_dag_args) as dag:

    Extract_file = PythonOperator(
        task_id='extract_file_from_server_to_gcs',
        python_callable=extract_file_from_server_to_gcs
    )

    Load_table = PythonOperator(
        task_id='load_table_from_gcs_to_bq',
        python_callable=load_table_from_gcs_to_bq
    )

    Transfer_data = BigQueryOperator(
        task_id='transfer_table_in_bq',
        sql='sql/main.sql',
        params={'LAKE_TABLE_NAME': f'{PROJECT_ID}.{LAKE_DATASET_ID}.HP-access-log-{day:%Y%m%d}',
                'DWH_TABLE_NAME': f'{PROJECT_ID}.{DWH_DATASET_ID}.daily_pv',
                'TARGET_DAY': day},
        use_legacy_sql=False
    )

    Extract_file >> Load_table >> Transfer_data
