# NetSuite REST API スクリプト
---

## 使えるまでの手順

1. **NetSuite で認証情報を取得**
   - 統合レコード (Setup > Integration > Manage Integrations): Consumer Key / Consumer Secret
   - アクセストークン (Setup > Users/Roles > Access Tokens): Token ID / Token Secret
   - Token-Based Authentication を有効化し、アクセストークンと統合レコードを紐付け

2. **依存パッケージのインストール**
   ```bash
   # macOS / Linux
   pip3 install -r scripts/requirements.txt
   # Windows
   pip install -r scripts/requirements.txt
   ```

3. **`.env` を作成**
   `.env.example` をコピーして `scripts/.env` を作成し、値を書き換える:
   ```bash
   cp scripts/.env.example scripts/.env
   ```
   ```
   NS_ACCOUNT_ID=1234567_SB1
   NS_CONSUMER_KEY=...
   NS_CONSUMER_SECRET=...
   NS_TOKEN_ID=...
   NS_TOKEN_SECRET=...
   ```
   サンドボックスは `1234567_SB1` 形式。本番は数値のみ。

4. **接続テスト**
   ```bash
   # macOS / Linux
   python3 scripts/export_metadata_from_rest.py --test-auth
   # Windows
   python scripts/export_metadata_from_rest.py --test-auth
   ```
   「認証成功」と出れば OK。

5. **メタデータをエクスポート**
   ```bash
   # macOS / Linux
   python3 scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item
   # Windows
   python scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item
   ```

6. **メタデータを検索**
   ```bash
   # macOS / Linux
   python3 scripts/query_metadata.py --env SB list-records
   # Windows
   python scripts/query_metadata.py --env SB list-records
   ```

---

### 想定ディレクトリ構成

```
<プロジェクトルート>/
├── scripts/                    # このディレクトリ
│   ├── .env.example            # 認証情報テンプレート
│   ├── .env                    # 認証情報（.env.exampleからコピーして作成）
│   ├── netsuite_client.py      # 共通モジュール
│   ├── export_metadata_from_rest.py
│   └── query_metadata.py
└── netsuite-metadata/          # エクスポート先（scripts の親直下）
    └── <ENV>/
        ├── records/
        └── manifest.json
```

---

## 共通モジュール

`netsuite_client.py` … `export_metadata_from_rest.py` で利用。認証（OAuth 1.0a）、設定読み込み、ベースURL取得。

---

## メタデータ エクスポート・検索

### export_metadata_from_rest.py

REST metadata-catalog からメタデータを取得し、`netsuite-metadata/<ENV>/` に保存。
（scripts の親ディレクトリ直下に netsuite-metadata を作成）

```bash
# 特定レコードのみ取得（推奨）
python3 scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item  # macOS/Linux
python  scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item  # Windows

# 全レコード取得
python3 scripts/export_metadata_from_rest.py --env SB  # macOS/Linux
python  scripts/export_metadata_from_rest.py --env SB  # Windows
```

### query_metadata.py

保存したメタデータを検索。

```bash
# macOS / Linux
python3 scripts/query_metadata.py --env SB list-records
python3 scripts/query_metadata.py --env SB get-record salesorder
python3 scripts/query_metadata.py --env SB suggest-suiteql salesorder --fields tranid,entity

# Windows
python scripts/query_metadata.py --env SB list-records
python scripts/query_metadata.py --env SB get-record salesorder
python scripts/query_metadata.py --env SB suggest-suiteql salesorder --fields tranid,entity
```

