# bq-cloud-composer

# 目的
Google Cloud Platformのサービスの1つであるCloud Composerを練習する。</br>
以前作成した[ETLパイプライン](https://github.com/zawa1120/bq-access-log)をCloud Composerで再現する。</br>
Cloud ComposerはKubernentesエンジンで動いているため、莫大な費用がかかる。今回作成したパイプラインはテストのために数日間動かし、その後は停止する。ログ収集は引き続き以前作成したパイプラインを運用する。

# ワークフロー
![composer](https://user-images.githubusercontent.com/58725085/169956198-d511bd5a-f48b-4f12-9053-55481e63c3de.png)


# 学んだこと&発見
1.Cloud Composerの基礎を手を動かしながら理解することができた。


2.Airflowに設定した環境変数とCloud Compoeserに設定した環境変数でそれぞれ取得方法が違う。具体的にどのように設定されているか調査が必要。そのためにもCloud Composerのアーキテクチャーを理解する必要がある。


3.DAGの`start_date`と`execution_date`、`schedule_interval`の関係性を手を動かしながら理解することができた。


4.SQL上で変数を扱う方法を学んだ。`use_legacy_sql`のパラメーターを`False`に指定することでStandardSQLを使用することができる。( SQLの最初の行に#standardSQLを記入しているがstandardsqlが使用されていない？ 要調査 )

# 試したこと
1.~~SSHOperatorとgsutilコマンドでログファイルを直接バケットに転送しようとした。しかし、rootユーザー以外にGCP関連のコマンドを使用させたくなかったのでこれを実現することが難しいと判断した。<br>
下記のコマンドを試してみたがsudoよりも先にgsutilの部分が展開され、「コマンドが見つかりません」とエラーを吐いてしまう。他に良い方法が見つかり次第、移行も検討する。~~


```sh
echo "パスワード" | sudo -S gsutil cp ファイル名 gs://バケット名
```


よく確認したらgsutilがエイリアスとして設定されていた。shellはエイリアスを子プロセスにまで適用しない。gsutil以降は子プロセスになるため、gsutilのシンボリックリンクを貼り替えるか、コマンドのファイルを直接指定することで回避することができた。


```sh
echo "パスワード" | sudo -S /root/google-cloud-sdk/bin/gsutil cp ファイル名 gs://バケット名
```

# 環境

macOS Big Sur 11.4 Apple M1

Google Cloud SDK 385.0.0
bq 2.0.74
core 2022.05.06
gsutil 5.10

Terraform v1.0.11
