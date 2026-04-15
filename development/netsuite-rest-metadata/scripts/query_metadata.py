#!/usr/bin/env python3
"""
query_metadata.py

NetSuite メタデータ (netsuite-metadata/<ENV>/) を検索する CLI ツール。
BYO Metadata Provider Contract 形式を想定。
（参照先: スクリプトの親ディレクトリ/netsuite-metadata/<env>/）

出力は JSON のみ。

参照: https://github.com/joshOrigami/netsuite-developer
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# スクリプトの親ディレクトリ直下の netsuite-metadata を参照
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BASE_DIR = PROJECT_ROOT / "netsuite-metadata"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_env(env: Optional[str]) -> str:
    if env:
        return env
    active_file = BASE_DIR / "active_env.json"
    if active_file.exists():
        data = load_json(active_file)
        return data.get("active_env", "")
    raise ValueError("Environment not specified. Use --env or create active_env.json")


def load_record_index(env: str) -> dict[str, Any]:
    return load_json(BASE_DIR / env / "record_index.json")


def load_record(env: str, record_key: str) -> dict[str, Any]:
    index = load_record_index(env)
    for rec in index["records"]:
        if rec["record_key"] == record_key:
            return load_json(BASE_DIR / env / rec["file"])
    raise ValueError(f"Record '{record_key}' not found in index.")


def list_records(env: str) -> dict[str, Any]:
    index = load_record_index(env)
    return {
        "environment": env,
        "records": [r["record_key"] for r in index["records"]],
    }


def list_fields(env: str, record_key: str) -> dict[str, Any]:
    record = load_record(env, record_key)
    return {
        "environment": env,
        "record_key": record_key,
        "fields": list(record.get("fields", {}).keys()),
    }


def find_field(env: str, field_id: str) -> dict[str, Any]:
    index = load_record_index(env)
    matches = []
    for rec in index["records"]:
        record = load_json(BASE_DIR / env / rec["file"])
        fields = record.get("fields", {})
        if field_id in fields:
            matches.append({
                "record_key": rec["record_key"],
                "field_definition": fields[field_id],
            })
    return {
        "environment": env,
        "field_id": field_id,
        "matches": matches,
    }


def suggest_suiteql(env: str, record_key: str, field_list: list[str]) -> dict[str, Any]:
    record = load_record(env, record_key)
    primary = record.get("primary_table", {})
    table = primary.get("suiteql_table")
    if not table:
        raise ValueError(f"No SuiteQL table defined for {record_key}")

    fields = record.get("fields", {})
    columns = []
    for f in field_list:
        if f not in fields:
            raise ValueError(f"Field '{f}' not found on {record_key}")
        col = fields[f].get("suiteql_column")
        if not col:
            raise ValueError(f"No SuiteQL column mapping for field '{f}'")
        columns.append(col)

    select_clause = ", ".join(columns)
    type_filter = primary.get("suiteql_type_filter")
    where_clause = f" WHERE type = '{type_filter}'" if type_filter else ""
    query = f"SELECT {select_clause} FROM {table}{where_clause}"
    return {
        "environment": env,
        "record_key": record_key,
        "suiteql": query,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query NetSuite metadata in netsuite-metadata/"
    )
    parser.add_argument("--env", help="Environment (e.g. SB, QA, PROD)")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-records")
    get_record_parser = subparsers.add_parser("get-record")
    get_record_parser.add_argument("record_key")
    list_fields_parser = subparsers.add_parser("list-fields")
    list_fields_parser.add_argument("record_key")
    find_field_parser = subparsers.add_parser("find-field")
    find_field_parser.add_argument("field_id")
    suiteql_parser = subparsers.add_parser("suggest-suiteql")
    suiteql_parser.add_argument("record_key")
    suiteql_parser.add_argument("--fields", required=True)

    args = parser.parse_args()

    try:
        env = resolve_env(args.env)
        if not env:
            raise ValueError("Environment not specified. Use --env <NAME>")

        if args.command == "list-records":
            result = list_records(env)
        elif args.command == "get-record":
            result = load_record(env, args.record_key)
        elif args.command == "list-fields":
            result = list_fields(env, args.record_key)
        elif args.command == "find-field":
            result = find_field(env, args.field_id)
        elif args.command == "suggest-suiteql":
            fields = [f.strip() for f in args.fields.split(",")]
            result = suggest_suiteql(env, args.record_key, fields)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
