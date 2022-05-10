import datetime
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from google.cloud import bigquery
from google.cloud import storage
from airflow import models
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator

PROJECT = models.Variable.get('PROJECT')
SOURCE_DATASET_ID = models.Variable.get('SOURCE_DATASET_ID')
DWH_DATASET_ID = models.Variable.get('DWH_DATASET_ID')
BUCKET = models.Variable.get('BUCKET')
SERVER_PORT = models.Variable.get('SERVER_PORT')
USERNAME = models.Variable.get('USERNAME')
PASSWORD = models.Variable.get('PASSWORD')

#day = datetime.datetime.now() - datetime.timedelta(days=1)
day = datetime.date(2022, 5, 5) # 今度消す
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

    gcs = storage.Client(PROJECT)
    bucket = gcs.get_bucket(BUCKET)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(f'/tmp/{file_name}')

def load_table_from_gcs_to_bq():
    bq = bigquery.Client(project=PROJECT)
    dataset = bq.dataset(SOURCE_DATASET_ID)

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
    'depends_on_past': False, # 今度消す
    'start_date': day
}

with models.DAG(
    dag_id = 'HP-access-log',
    schedule_interval = None,
    # schedule_interval = '0 12 0 0 0',
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
        params={'SOURCE_TABLE_NAME': f'{PROJECT}.{SOURCE_DATASET_ID}.access-log-{day:%Y%m%d}',
                'DWH_TABLE_NAME': f'{PROJECT}.{DWH_DATASET_ID}.daily_pv',
                'TARGET_DAY': day}
    )

    Extract_file >> Load_table >> Transfer_data
