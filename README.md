# openstack-opendev-merge-summary

このリポジトリには、OpenStackの開発基盤である [opendev](https://review.opendev.org) からマージされた詳細を取得し、JSON形式で要約を出力するためのカスタムスクリプト。Gerrit APIのエンドポイントを使用して、マージされた情報のタイトル、作成者、コミットメッセージなどの情報を取得します。取得するのは、変更が最後に更新されてからの経過時間を指定可能とします。

## 使い方

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 基本的な使用方法

```bash
python3 get_merged_diffs.py
```

### 環境変数による設定

以下の環境変数で動作をカスタマイズできます：

- `REPO_NAME`: 対象リポジトリ（デフォルト: `openstack/barbican`）
- `STATUS`: ステータスフィルター（デフォルト: `merged`）
- `AGE`: 期間フィルター（デフォルト: `1d`）
- `DRY_RUN`: `true`に設定するとAPIコールを行わずクエリのみ表示

### 使用例

```bash
# デフォルト設定（openstack/barbican、過去1日のマージ済み変更）
python3 get_merged_diffs.py

# 異なるリポジトリを指定
REPO_NAME=openstack/nova python3 get_merged_diffs.py

# 過去7日間のオープンな変更を取得
STATUS=open AGE=7d python3 get_merged_diffs.py

# ドライランモード（APIコールなし）
DRY_RUN=true python3 get_merged_diffs.py

# 複数の設定を組み合わせ
REPO_NAME=openstack/keystone STATUS=merged AGE=3d python3 get_merged_diffs.py
```

## 出力形式

スクリプトは以下の形式でJSONを出力します：

```json
{
  "query": "status:merged+repo:openstack/barbican+age:1d",
  "count": 2,
  "repository": "openstack/barbican",
  "status": "merged",
  "age": "1d",
  "timestamp": "2024-01-01T12:00:00.000000",
  "changes": [
    {
      "id": "change-id",
      "subject": "変更のタイトル",
      "status": "MERGED",
      "owner": {...},
      "created": "...",
      "updated": "...",
      "submitted": "...",
      "revision_id": "...",
      "files": [
        {
          "path": "path/to/file.py",
          "status": "success",
          "diff": {...}
        }
      ]
    }
  ]
}
```
