#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetSuite REST API 接続の共通モジュール

認証方式: OAuth 1.0a Token-Based Authentication (TBA)
環境変数: NS_ACCOUNT_ID, NS_CONSUMER_KEY, NS_CONSUMER_SECRET, NS_TOKEN_ID, NS_TOKEN_SECRET
"""

import os
import sys
from pathlib import Path

from requests_oauthlib import OAuth1


def load_config(env_path_hint: str = ".env") -> dict[str, str]:
    """
    認証情報を環境変数から読み込む
    .env はスクリプトと同じディレクトリを優先
    """
    try:
        from dotenv import load_dotenv

        script_dir = Path(__file__).resolve().parent
        env_file = script_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
    except ImportError:
        pass

    required = [
        "NS_ACCOUNT_ID",
        "NS_CONSUMER_KEY",
        "NS_CONSUMER_SECRET",
        "NS_TOKEN_ID",
        "NS_TOKEN_SECRET",
    ]
    config = {}
    for key in required:
        val = os.environ.get(key)
        if not val:
            print(
                f"エラー: 環境変数 {key} が設定されていません。\n"
                f"{env_path_hint} を設定するか、環境変数を設定してください。"
            )
            sys.exit(1)
        config[key] = val.strip().strip('"').strip("'")

    return config


def create_netsuite_client(config: dict[str, str]) -> OAuth1:
    """OAuth 1.0a クライアントを作成（requests_oauthlib 使用）"""
    return OAuth1(
        client_key=config["NS_CONSUMER_KEY"],
        client_secret=config["NS_CONSUMER_SECRET"],
        resource_owner_key=config["NS_TOKEN_ID"],
        resource_owner_secret=config["NS_TOKEN_SECRET"],
        realm=config["NS_ACCOUNT_ID"],
        signature_method="HMAC-SHA256",
    )


def get_base_url(account_id: str) -> str:
    """
    NetSuite REST API のベースURL
    例: '9348653_SB4' -> 'https://9348653-sb4.suitetalk.api.netsuite.com/services/rest/record/v1'
    """
    host_id = account_id.lower().replace("_", "-")
    return f"https://{host_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
