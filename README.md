# openstack-opendev-merge-summary

このリポジトリには、OpenStackの開発基盤であるopendev(https://review.opendev.org)からマージされた詳細を取得し、JSON形式で要約を出力するためのカスタムスクリプト。Gerrit APIのエンドポイントを使用して、マージされた情報のタイトル、作成者、コミットメッセージなどの情報を取得します。取得するのは、変更が最後に更新されてからの経過時間を指定可能とします。
