#!/usr/bin/env python3
"""
OpenStack OpenDev Merge Summary Script

This script fetches merged diff information from OpenStack repositories
via Gerrit REST API and outputs the changes data as JSON.

Environment Variables:
- OPENDEV_REPO_NAME: Repository name (default: openstack/barbican)
- OPENDEV_STATUS: Status filter (default: merged)
- OPENDEV_MERGED_AFTER: Merged after date in YYYY-MM-DD format (default: calculated from age)
- OPENDEV_AGE: Age filter (default: 1d) - converted to mergedafter date
- OPENDEV_DRY_RUN: If set to 'true', only show query without making API calls
- OPENDEV_LOG: If set to 'true', show debug and info messages (default: false)
"""

import requests
import json
import urllib.parse
import os
import sys
from datetime import datetime, timedelta
import re

def log_message(message, file=sys.stderr):
    """
    Print log message only if OPENDEV_LOG environment variable is set to 'true'.
    
    Args:
        message (str): Message to log
        file: Output file (default: sys.stderr)
    """
    if os.getenv('OPENDEV_LOG', '').lower() == 'true':
        print(message, file=file)

def parse_age_to_date(age_str):
    """
    Parse age string (like '1d', '7d', '30d') to a date string in YYYY-MM-DD format.
    
    Args:
        age_str (str): Age string like '1d', '7d', '30d'
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    if not age_str:
        age_str = '1d'
    
    # Parse the age string using regex
    match = re.match(r'^(\d+)([dhm])$', age_str.lower())
    if not match:
        # If parsing fails, default to 1 day
        days = 1
    else:
        number = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'd':
            days = number
        elif unit == 'h':
            days = max(1, number // 24)  # Convert hours to days, minimum 1 day
        elif unit == 'm':
            days = max(1, number // (24 * 60))  # Convert minutes to days, minimum 1 day
        else:
            days = 1
    
    # Calculate the date
    target_date = datetime.now() - timedelta(days=days)
    return target_date.strftime('%Y-%m-%d')

def get_merged_diffs():
    """
    Gerrit REST APIを使用して、指定された条件でマージされた
    リポジトリの変更の差分を取得し、JSON形式で出力します。
    """
    # 環境変数から設定を取得（デフォルト値付き）
    repo_name = os.getenv('OPENDEV_REPO_NAME', 'openstack/barbican')
    status = os.getenv('OPENDEV_STATUS', 'merged')
    merged_after = os.getenv('OPENDEV_MERGED_AFTER')
    age = os.getenv('OPENDEV_AGE', '1d')
    dry_run = os.getenv('OPENDEV_DRY_RUN', '').lower() == 'true'
    
    # merged_afterが指定されていない場合は、ageから変換
    if not merged_after:
        merged_after = parse_age_to_date(age)
    
    gerrit_url = 'https://review.opendev.org'
    
    # 検索クエリを構築
    query = f'status:{status} repo:{repo_name} mergedafter:{merged_after}'
    
    log_message(f"Searching for changes: {query}")
    
    if dry_run:
        log_message("DRY_RUN mode: Skipping API calls")
        return {
            'query': query,
            'count': 0,
            'repository': repo_name,
            'status': status,
            'merged_after': merged_after,
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
        log_message(f"指定された条件 ({query}) でマージされた変更は見つかりませんでした。")
        return {"changes": [], "query": query, "count": 0}

    log_message(f"条件に一致する変更を {len(changes)} 件見つけました。")
    
    result_changes = []
    
    for change in changes:
        change_id = change['id']
        change_subject = change['subject']
        
        log_message(f"\n--- 変更を処理中: {change_subject} ({change_id}) ---")

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
                log_message("この変更にはファイル変更が含まれていません。")
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
                    log_message(f"ファイル差分を取得しました: {file_path}")
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
        'merged_after': merged_after,
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