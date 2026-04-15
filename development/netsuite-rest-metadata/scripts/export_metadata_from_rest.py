#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetSuite REST API metadata-catalog からメタデータを取得し、
netsuite-metadata/<ENV>/ に保存するスクリプト。
（出力先: スクリプトの親ディレクトリ/netsuite-metadata/<env>/）

使い方:
  python export_metadata_from_rest.py --env SB
  python export_metadata_from_rest.py --env QA --select salesorder,customer,item
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# 同ディレクトリの netsuite_client を import できるようにする
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import requests

from netsuite_client import create_netsuite_client, get_base_url, load_config

# REST record type -> (suiteql_table, suiteql_type_filter)
SUITEQL_MAPPING: dict[str, tuple[str, Optional[str]]] = {
    "salesorder": ("transaction", "SalesOrd"),
    "invoice": ("transaction", "CustInvc"),
    "purchaseorder": ("transaction", "PurchOrd"),
    "itemfulfillment": ("transaction", "ItemFulfillment"),
    "transaction": ("transaction", None),
    "customer": ("customer", None),
    "vendor": ("vendor", None),
    "item": ("item", None),
    "employee": ("employee", None),
    "subsidiary": ("subsidiary", None),
    "department": ("department", None),
    "class": ("class", None),
    "location": ("location", None),
    "account": ("account", None),
    "currency": ("currency", None),
}

FIELD_TYPE_MAP: dict[str, str] = {
    "integer": "integer",
    "number": "number",
    "string": "text",
    "boolean": "boolean",
    "object": "record_ref",
    "array": "multi_select",
}


def _get_suiteql_mapping(record_key: str) -> tuple[str, Optional[str]]:
    """レコードキーから SuiteQL テーブル・型フィルタを取得"""
    key_lower = record_key.lower()
    if key_lower in SUITEQL_MAPPING:
        return SUITEQL_MAPPING[key_lower]
    if key_lower.startswith("customrecord"):
        return (key_lower, None)
    return (record_key, None)


def _schema_type_to_field_type(prop: dict) -> str:
    """JSON Schema property から BYO field_type を推定"""
    json_type = prop.get("type", "string")
    fmt = prop.get("format", "")
    if "$ref" in prop or (json_type == "object" and "properties" not in prop):
        return "record_ref"
    if json_type == "array":
        return "multi_select"
    if fmt == "date":
        return "date"
    if fmt == "date-time":
        return "datetime"
    if fmt == "int64":
        return "integer"
    return FIELD_TYPE_MAP.get(json_type, "text")


def _extract_ref_target(ref: str) -> Optional[str]:
    """$ref からターゲットレコードタイプを抽出"""
    if not ref:
        return None
    parts = ref.split("/")
    return parts[-1] if parts else None


def fetch_metadata_catalog_list(
    config: dict[str, str], select: Optional[list[str]] = None
) -> list[str]:
    """metadata-catalog のレコードタイプ一覧を取得"""
    base_url = get_base_url(config["NS_ACCOUNT_ID"])
    url = f"{base_url}/metadata-catalog"
    if select:
        url += "?select=" + ",".join(select)

    auth = create_netsuite_client(config)
    headers = {"Accept": "application/json"}
    resp = requests.get(url, auth=auth, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"エラー: metadata-catalog 取得失敗 HTTP {resp.status_code}")
        print(resp.text[:500] if resp.text else "")
        if resp.status_code == 401:
            print(
                "\n認証エラーの場合: 同一ディレクトリの .env のトークンが有効か確認してください。"
                "\n  export_metadata_from_rest.py --test-auth で接続テストできます。"
            )
        sys.exit(1)

    data = resp.json()
    items = data.get("items", [])
    return [item["name"] for item in items]


def fetch_record_schema(
    config: dict[str, str], record_type: str
) -> Optional[dict[str, Any]]:
    """指定レコードの JSON Schema を取得"""
    base_url = get_base_url(config["NS_ACCOUNT_ID"])
    url = f"{base_url}/metadata-catalog/{record_type}"

    auth = create_netsuite_client(config)
    headers = {"Accept": "application/schema+json"}
    resp = requests.get(url, auth=auth, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"  警告: {record_type} 取得失敗 HTTP {resp.status_code}")
        return None

    return resp.json()


def convert_schema_to_byo(
    record_key: str, schema: dict[str, Any]
) -> dict[str, Any]:
    """NetSuite JSON Schema を BYO 形式に変換"""
    table, type_filter = _get_suiteql_mapping(record_key)
    primary_table: dict[str, Any] = {"suiteql_table": table}
    if type_filter:
        primary_table["suiteql_type_filter"] = type_filter

    fields: dict[str, dict] = {}
    props = schema.get("properties", {})

    for field_id, prop in props.items():
        field_type = _schema_type_to_field_type(prop)
        field_def: dict[str, Any] = {
            "label": prop.get("title", field_id),
            "field_type": field_type,
            "nullable": prop.get("nullable", True),
            "suiteql_column": field_id,
        }
        ref = prop.get("$ref")
        if ref:
            target = _extract_ref_target(ref)
            if target:
                field_def["ref"] = {
                    "target_record_key": target,
                    "relationship": "many_to_one",
                }
        if prop.get("x-ns-custom-field"):
            field_def["custom"] = True
        fields[field_id] = field_def

    return {
        "record_key": record_key,
        "record_type": record_key,
        "label": record_key.replace("_", " ").title(),
        "record_family": "custom" if record_key.lower().startswith("customrecord") else "standard",
        "primary_table": primary_table,
        "fields": fields,
        "capabilities": {"suiteql": True, "rest_record": True, "sdf": True},
    }


def export_metadata(
    env: str,
    config: dict[str, str],
    select: Optional[list[str]] = None,
) -> None:
    """メタデータを取得して netsuite-metadata/<env>/ に保存"""
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "netsuite-metadata" / env
    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    print(f"metadata-catalog からレコード一覧を取得中...")
    record_types = fetch_metadata_catalog_list(config, select)
    print(f"  取得: {len(record_types)} 件")
    if select and record_types:
        print(f"  対象: {record_types}")

    record_index: list[dict] = []
    success_count = 0

    for rt in record_types:
        print(f"  {rt} を取得中...", end=" ")
        schema = fetch_record_schema(config, rt)
        if not schema:
            print("スキップ")
            continue

        byo = convert_schema_to_byo(rt, schema)
        record_file = records_dir / f"{rt}.json"
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(byo, f, indent=2, ensure_ascii=False)
        record_index.append({
            "record_key": rt,
            "record_type": rt,
            "record_family": byo.get("record_family", "standard"),
            "label": byo.get("label", rt),
            "file": f"records/{rt}.json",
        })
        success_count += 1
        print("OK")

    with open(output_dir / "record_index.json", "w", encoding="utf-8") as f:
        json.dump({"records": record_index}, f, indent=2, ensure_ascii=False)

    account_id = config["NS_ACCOUNT_ID"].replace("_SB4", "").replace("_SB1", "")
    manifest = {
        "contract_version": "1.0.0",
        "provider": {"name": "rest-metadata-export", "version": "1.0.0"},
        "source": {
            "system": "netsuite",
            "account_id": account_id,
            "account_name": "",
            "environment": env,
        },
        "app_context": {
            "app_id": "export_metadata_from_rest",
            "app_version": "1.0.0",
            "export_scope": "schema_only",
            "feature_flags": [],
        },
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_classification": "schema_only",
        "notes": "Exported from NetSuite REST metadata-catalog. No transactional data. No PII.",
    }
    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n完了: {success_count} 件のレコードを {output_dir} に保存しました。")
    print(f"  query_metadata.py で利用できます:")
    print(f"    python query_metadata.py --env {env} list-records")


def test_auth(config: dict[str, str]) -> bool:
    """認証テスト（metadata-catalog に GET を送信）"""
    base_url = get_base_url(config["NS_ACCOUNT_ID"])
    url = f"{base_url}/metadata-catalog"
    auth = create_netsuite_client(config)
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, auth=auth, headers=headers, timeout=30)
        if resp.status_code == 200:
            print("認証成功: metadata-catalog に接続できました。")
            return True
        print(f"認証失敗: HTTP {resp.status_code}")
        if resp.text:
            print(resp.text[:500])
        return False
    except requests.exceptions.RequestException as e:
        print(f"接続エラー: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NetSuite REST metadata-catalog からメタデータをエクスポート"
    )
    parser.add_argument(
        "--env",
        help="環境名 (例: SB, QA, PROD)。出力先 netsuite-metadata/<env>/",
    )
    parser.add_argument(
        "--select",
        type=str,
        help="取得するレコードタイプをカンマ区切りで指定 (例: salesorder,customer,item)",
    )
    parser.add_argument(
        "--test-auth",
        action="store_true",
        help="認証テストのみ実行（接続可否を確認）",
    )
    args = parser.parse_args()

    config = load_config()

    if args.test_auth:
        ok = test_auth(config)
        sys.exit(0 if ok else 1)

    if not args.env:
        parser.error("--env は必須です（--test-auth を除く）")

    select_list = None
    if args.select:
        select_list = [s.strip() for s in args.select.split(",") if s.strip()]

    export_metadata(args.env, config, select_list)


if __name__ == "__main__":
    main()
