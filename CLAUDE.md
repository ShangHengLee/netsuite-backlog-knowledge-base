# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

NetSuiteに関する社内ナレッジベース（Backlog）を蓄積・整理するためのドキュメントリポジトリ。
開発（SuiteScript、カスタマイズ）のみならず、NetSuiteの運用・設定・機能全般にわたる社内ノウハウを文章化する。

## 目的

- 社内メンバーが参照できるNetSuiteのナレッジを体系的にドキュメント化
- テーマごとにフォルダを分けて管理
- 将来的な社内オンボーディングや業務標準化への活用

## 関連リソース

- **既存Backlog整理スクリプト**:
  `/Users/truegentlaman/Library/CloudStorage/GoogleDrive-lee.heng@shearwaterasia.com/マイドライブ/document/NSKnowledgeBase/scripts`
  → 社内Backlogをダウンロード・整理するPJフォルダ。ドキュメント構成の参考として必要に応じて参照すること。

## ドキュメント構成方針

- テーマ（機能・領域）ごとにサブフォルダを作成
- 各フォルダ内にMarkdown形式でドキュメントを配置
- 想定読者：社内のNetSuite関係者（スキルレベルは文書ごとに明記）

## 現在のフォルダ構成

```
backlogPJ/
└── development/
    ├── netsuite-rest-metadata.md   # REST APIによるメタデータ取得の解説
    └── scripts/                    # 解説で紹介しているサンプルスクリプト群
        ├── netsuite_client.py          # OAuth 1.0a 認証の共通モジュール
        ├── export_metadata_from_rest.py # メタデータ取得・エクスポート
        ├── query_metadata.py            # メタデータ検索・SuiteQL生成
        ├── create_customer.py           # Customerレコード作成サンプル
        └── requirements.txt
```

## scripts/ の実行方法

スクリプトを実際に動かす場合は `scripts/.env` を作成して認証情報を設定する。

```
NS_ACCOUNT_ID=1234567_SB1
NS_CONSUMER_KEY=...
NS_CONSUMER_SECRET=...
NS_TOKEN_ID=...
NS_TOKEN_SECRET=...
```

```bash
# 依存パッケージのインストール
pip3 install requests requests-oauthlib python-dotenv

# 接続テスト
python3 development/scripts/export_metadata_from_rest.py --test-auth

# メタデータ取得
python3 development/scripts/export_metadata_from_rest.py --env SB --select salesorder,customer
```
