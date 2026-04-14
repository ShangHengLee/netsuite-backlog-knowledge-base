#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetSuite REST API を使用して Customer レコードを新規作成する Python スクリプト

認証方式: OAuth 1.0a Token-Based Authentication (TBA)
使用する認証情報:
  - ACCOUNT_ID: NetSuite アカウントID (例: 1234567 または 1234567_SB1 for Sandbox)
  - CONSUMER_KEY: 統合レコードの消費者キー
  - CONSUMER_SECRET: 統合レコードの消費者シークレット
  - TOKEN_ID: アクセストークンID
  - TOKEN_SECRET: アクセストークンシークレット

環境変数または .env ファイルで設定してください。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

# 同ディレクトリの netsuite_client を import できるようにする
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import requests

from netsuite_client import (
    create_netsuite_client,
    get_base_url,
    load_config,
)


def create_customer(
    customer_data: dict[str, Any],
    config: dict[str, str],
) -> Optional[dict[str, Any]]:
    """
    NetSuite REST API で Customer レコードを新規作成する

    Args:
        customer_data: Customer レコードのデータ
        config: 認証設定

    Returns:
        成功時: 作成されたレコードのメタデータ（Location ヘッダーから取得したIDなど）
        失敗時: None
    """
    account_id = config["NS_ACCOUNT_ID"]
    base_url = get_base_url(account_id)
    url = f"{base_url}/customer"

    debug = os.environ.get("NS_DEBUG", "").lower() in ("1", "true", "yes")
    if debug:
        print(f"[DEBUG] 接続先: {url}")

    # requests_oauthlib を使用（export_metadata_from_rest.py と同様。手動 OAuth は 401 になりやすい）
    auth = create_netsuite_client(config)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(
        url,
        auth=auth,
        headers=headers,
        json=customer_data,
    )

    if response.status_code in (200, 201, 204):
        # 204 No Content の場合はレスポンスボディが空
        location = response.headers.get("Location")
        if location:
            # Location ヘッダーに作成されたリソースのURLが含まれる
            return {"location": location, "status_code": response.status_code}
        return {"status_code": response.status_code}
    else:
        print(f"エラー: HTTP {response.status_code}")
        try:
            error_detail = response.json()
            print(json.dumps(error_detail, indent=2, ensure_ascii=False))
        except Exception:
            print(response.text)
        if response.status_code == 401:
            print(
                "\n【401 認証エラーの確認ポイント】\n"
                "■ Login Audit Trail に記録がない場合:\n"
                "  リクエストが別のNetSuiteアカウントに向かっている可能性があります。\n"
                "  python create_customer.py --test-auth で接続先URLを確認し、\n"
                "  ログイン中のNetSuite（Setup > Company > Company Information > Company URLs）と一致するか確認してください。\n"
                "  サンドボックスの場合は NS_ACCOUNT_ID が 1234567_SB1 形式になっているか確認。\n"
                "\n■ その他の確認:\n"
                "1. Login Audit Trail で Use Advanced Search を有効にし、\n"
                "   Results に Detail / Token-based Access Token Name / Token-based Application Name を追加\n"
                "2. Consumer Key/Secret と Token ID/Secret に余分な空白がないか確認\n"
                "3. 統合レコードの「Token-Based Authentication」が有効か確認\n"
                "4. アクセストークンが統合レコードと紐付いているか確認\n"
                "5. PCの時刻が正しいか確認（5分以上のズレで失敗する場合があります）"
            )
        return None


def check_reachability(config: dict[str, str]) -> bool:
    """
    認証なしで NetSuite エンドポイントに到達できるか確認
    401 が返れば NetSuite まで届いている（記録が残らない場合の切り分け用）
    """
    base_url = get_base_url(config["NS_ACCOUNT_ID"])
    url = f"{base_url}/customer?limit=1"
    print(f"到達確認: {url}")
    print("（認証なしでリクエスト送信）")
    try:
        response = requests.get(url, timeout=10)
        print(f"HTTP {response.status_code} - レスポンスヘッダー:")
        for k, v in response.headers.items():
            print(f"  {k}: {v[:80]}{'...' if len(str(v)) > 80 else ''}")
        if response.status_code == 401:
            print("\n→ 401 が返りました。リクエストは NetSuite に届いています。")
            print("  記録が残らないのは、認証失敗が NetSuite の監査対象外である可能性があります。")
        elif response.status_code in (200, 204):
            print("\n→ 認証なしで成功？ 想定外です。")
        else:
            print(f"\n→ 想定外のステータス。プロキシやファイアウォールの可能性があります。")
        return True
    except requests.exceptions.RequestException as e:
        print(f"接続エラー: {e}")
        print("\n→ NetSuite に到達できていません。ファイアウォール、プロキシ、VPN を確認してください。")
        return False


def test_auth(config: dict[str, str], verbose: bool = False) -> bool:
    """
    認証のテスト（GET で Customer 一覧の先頭1件を取得）
    成功すれば認証情報は正しい
    """
    base_url = get_base_url(config["NS_ACCOUNT_ID"])
    url = f"{base_url}/customer?limit=1"

    auth = create_netsuite_client(config)
    headers = {"Accept": "application/json"}
    response = requests.get(url, auth=auth, headers=headers)

    if response.status_code in (200, 204):
        print("認証成功: 接続は正常です")
        return True
    print(f"認証失敗: HTTP {response.status_code}")
    if verbose:
        print("レスポンスヘッダー:")
        for k, v in response.headers.items():
            print(f"  {k}: {v[:80]}{'...' if len(str(v)) > 80 else ''}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)
    return False


def main() -> None:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    if "--verbose" in sys.argv:
        sys.argv.remove("--verbose")
    if "-v" in sys.argv:
        sys.argv.remove("-v")

    if "--check-reach" in sys.argv:
        config = load_config()
        ok = check_reachability(config)
        sys.exit(0 if ok else 1)

    if "--test-auth" in sys.argv:
        config = load_config()
        base_url = get_base_url(config["NS_ACCOUNT_ID"])
        url = f"{base_url}/customer?limit=1"
        print(f"接続先: {url}")
        print(
            "※ 記録が残らない場合: --check-reach で NetSuite 到達を確認できます。"
        )
        print("認証をテストしています...")
        ok = test_auth(config, verbose=verbose)
        sys.exit(0 if ok else 1)

    config = load_config()

    # NetSuiteの定義: フィールド名は小文字
    customer_data = {
        "companyname": "サンプル株式会社", # companyName ではなく companyname
        "subsidiary": {"id": "1"},       # 多くの環境で必須項目です
        "email": "contact@sample.example.com",
    }

    # コマンドライン引数で顧客データを上書きできるようにする
    if len(sys.argv) > 1:
        try:
            override = json.loads(sys.argv[1])
            customer_data.update(override)
        except json.JSONDecodeError:
            print("警告: 引数は有効なJSON形式で指定してください")

    print("Customer レコードを作成しています...")
    result = create_customer(customer_data, config)

    if result:
        print("成功: Customer レコードが作成されました。")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
