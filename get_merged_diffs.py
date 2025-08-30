#!/usr/bin/env python3
"""
OpenStack OpenDev Merge Summary Script

This script fetches merged diff information from OpenStack repositories
via Gerrit REST API and outputs the changes data as JSON.

Environment Variables:
- REPO_NAME: Repository name (default: openstack/barbican)
- STATUS: Status filter (default: merged)
- AGE: Age filter (default: 1d)
- DRY_RUN: If set to 'true', only show query without making API calls
"""

import requests
import json
import urllib.parse
import os
import sys
from datetime import datetime, timedelta

def get_merged_diffs():
    """
    Gerrit REST APIを使用して、指定された条件でマージされた
    リポジトリの変更の差分を取得し、JSON形式で出力します。
    """
    # 環境変数から設定を取得（デフォルト値付き）
    repo_name = os.getenv('REPO_NAME', 'openstack/barbican')
    status = os.getenv('STATUS', 'merged')
    age = os.getenv('AGE', '1d')
    dry_run = os.getenv('DRY_RUN', '').lower() == 'true'
    
    gerrit_url = 'https://review.opendev.org'
    
    # 検索クエリを構築
    query = f'status:{status}+repo:{repo_name}+age:{age}'
    
    print(f"Searching for changes: {query}", file=sys.stderr)
    
    if dry_run:
        print("DRY_RUN mode: Skipping API calls", file=sys.stderr)
        return {
            'query': query,
            'count': 0,
            'repository': repo_name,
            'status': status,
            'age': age,
            'timestamp': datetime.now().isoformat(),
            'changes': [],
            'dry_run': True
        }
    
    # Gerrit APIのエンドポイント
    changes_endpoint = f'{gerrit_url}/changes/'
    
    try:
        # 変更リストをクエリするAPIリクエスト
        # 応答の不正なプレフィックス `)]}'` を処理します。
        response = requests.get(
            changes_endpoint, 
            params={'q': query, 'o': 'ALL_REVISIONS'},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # JSONレスポンスからプレフィックスを削除
        changes = json.loads(response.text[4:])
        
    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSONデコード中にエラーが発生しました: {e}", file=sys.stderr)
        return None

    if not changes:
        print(f"指定された条件 ({query}) でマージされた変更は見つかりませんでした。", file=sys.stderr)
        return {"changes": [], "query": query, "count": 0}

    print(f"条件に一致する変更を {len(changes)} 件見つけました。", file=sys.stderr)
    
    result_changes = []
    
    for change in changes:
        change_id = change['id']
        change_subject = change['subject']
        
        print(f"\n--- 変更を処理中: {change_subject} ({change_id}) ---", file=sys.stderr)

        # 最新のリビジョンIDを取得します
        revision_id = change['current_revision']
        
        change_data = {
            'id': change_id,
            'subject': change_subject,
            'status': change.get('status'),
            'owner': change.get('owner', {}),
            'created': change.get('created'),
            'updated': change.get('updated'),
            'submitted': change.get('submitted'),
            'revision_id': revision_id,
            'files': []
        }
        
        try:
            # 特定のリビジョンで変更されたファイルリストを取得します
            files_endpoint = f'{changes_endpoint}{change_id}/revisions/{revision_id}/files/'
            files_response = requests.get(files_endpoint)
            files_response.raise_for_status()
            
            # レスポンスのJSONからプレフィックスを削除
            files = json.loads(files_response.text[4:])
            
            # 差分を取得しない特殊なキーをスキップ（/COMMIT_MSGなど）
            file_paths = [path for path in files.keys() if not path.startswith('/')]
            
            if not file_paths:
                print("この変更にはファイル変更が含まれていません。", file=sys.stderr)
                change_data['files'] = []
                result_changes.append(change_data)
                continue
            
            for file_path in file_paths:
                encoded_file_path = urllib.parse.quote(file_path, safe='')
                
                # 個々のファイルの差分を取得するAPIリクエスト
                diff_endpoint = f'{changes_endpoint}{change_id}/revisions/{revision_id}/files/{encoded_file_path}/diff'
                diff_response = requests.get(diff_endpoint)
                
                file_data = {
                    'path': file_path,
                    'status': 'success' if diff_response.status_code == 200 else 'error',
                    'diff': None
                }
                
                if diff_response.status_code == 200:
                    try:
                        # 差分コンテンツをJSONとして解析
                        file_data['diff'] = json.loads(diff_response.text[4:])
                    except json.JSONDecodeError:
                        # JSONでない場合はテキストとして保存
                        file_data['diff'] = diff_response.text
                    print(f"ファイル差分を取得しました: {file_path}", file=sys.stderr)
                else:
                    file_data['error_code'] = diff_response.status_code
                    print(f"差分情報の取得に失敗しました: {file_path}. ステータスコード: {diff_response.status_code}", file=sys.stderr)
                
                change_data['files'].append(file_data)

        except requests.exceptions.RequestException as e:
            print(f"ファイルの差分取得中にエラーが発生しました: {e}", file=sys.stderr)
            change_data['error'] = str(e)
        
        result_changes.append(change_data)

    # 結果をJSON形式で構造化
    result = {
        'query': query,
        'count': len(result_changes),
        'repository': repo_name,
        'status': status,
        'age': age,
        'timestamp': datetime.now().isoformat(),
        'changes': result_changes
    }
    
    return result

def main():
    """メイン関数"""
    result = get_merged_diffs()
    
    if result is not None:
        # JSON形式で出力（標準エラー出力でログ、標準出力でJSON）
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()