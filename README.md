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

- `OPENDEV_REPO_NAME`: 対象リポジトリ（デフォルト: `openstack/barbican`）
- `OPENDEV_STATUS`: ステータスフィルター（デフォルト: `merged`）
- `OPENDEV_MERGED_AFTER`: マージされた日付の下限をYYYY-MM-DD形式で指定（デフォルト: ageから計算）
- `OPENDEV_AGE`: 期間フィルター（デフォルト: `1d`）- merged_after日付に変換されます
- `OPENDEV_DRY_RUN`: `true`に設定するとAPIコールを行わずクエリのみ表示

### 使用例

```bash
# デフォルト設定（openstack/barbican、過去1日のマージ済み変更）
python3 get_merged_diffs.py

# 異なるリポジトリを指定
OPENDEV_REPO_NAME=openstack/nova python3 get_merged_diffs.py

# 過去7日間のオープンな変更を取得
OPENDEV_STATUS=open OPENDEV_AGE=7d python3 get_merged_diffs.py

# 特定の日付以降のマージ済み変更を取得
OPENDEV_MERGED_AFTER=2025-01-01 python3 get_merged_diffs.py

# ドライランモード（APIコールなし）
OPENDEV_DRY_RUN=true python3 get_merged_diffs.py

# 複数の設定を組み合わせ
OPENDEV_REPO_NAME=openstack/keystone OPENDEV_STATUS=merged OPENDEV_AGE=3d python3 get_merged_diffs.py
```

## 出力形式

スクリプトは以下の形式でJSONを出力します：

```json
{
  "query": "status:merged repo:openstack/barbican mergedafter:2025-08-29",
  "count": 2,
  "repository": "openstack/barbican",
  "status": "merged",
  "merged_after": "2025-08-29",
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
