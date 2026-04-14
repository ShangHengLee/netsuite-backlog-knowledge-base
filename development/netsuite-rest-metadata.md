# NetSuite REST API によるメタデータ取得の仕組み

## 概要

NetSuiteが提供するREST APIの **metadata-catalog** エンドポイントを使うことで、SalesOrderやCustomerといった各レコードのフィールド定義（スキーマ情報）をローカルに取得・保存できる。

これにより以下のことが可能になる：

- レコードに存在するフィールド一覧の確認
- 各フィールドのデータ型・参照先レコードの確認
- **SuiteQLクエリの自動生成**（フィールド名を指定するだけでSELECT文を生成）
- AIツール（Claude等）への入力データとして活用

毎回NetSuiteの画面でフィールドを調べる手間を省き、開発・クエリ作成を効率化するための仕組みです。

---

## 仕組みの全体像

```
NetSuite (REST API)
  └── /services/rest/record/v1/metadata-catalog
          │
          │  OAuth 1.0a (TBA) で認証
          │
          ↓
  export_metadata_from_rest.py
          │
          │  JSON Schema → BYO形式に変換して保存
          │
          ↓
  netsuite-metadata/<ENV>/
    ├── records/
    │   ├── salesorder.json
    │   ├── customer.json
    │   └── ...
    ├── record_index.json
    └── manifest.json
          │
          ↓
  query_metadata.py
    └── フィールド検索・SuiteQL生成
```

---

## 認証：OAuth 1.0a Token-Based Authentication (TBA)

NetSuiteのREST APIはOAuth 1.0aのTBA方式を採用している。ユーザーのログインセッションではなく、**統合レコード（Integration）とアクセストークン**の組み合わせで認証する。

### 4つの認証情報

| 項目 | 説明 | 取得場所 |
|------|------|----------|
| Consumer Key | 統合レコードを識別するID | Setup > Integration > Manage Integrations |
| Consumer Secret | 統合レコードのシークレット | 同上（作成時のみ表示） |
| Token ID | アクセストークンのID | Setup > Users/Roles > Access Tokens |
| Token Secret | アクセストークンのシークレット | 同上（作成時のみ表示） |

加えて **Account ID**（例：`1234567` または `1234567_SB1`）が必要。

> **注意:** Consumer SecretとToken Secretは作成直後しか表示されない。必ずメモしておくこと。

### 署名方式

`HMAC-SHA256` を使用。リクエストごとにタイムスタンプとnonceが生成され、署名が計算される（`requests-oauthlib` ライブラリが処理する）。

---

## NetSuiteでの事前設定

### 1. Token-Based Authentication の有効化

`Setup > Company > Enable Features > SuiteCloud` タブで **Token-Based Authentication** にチェックを入れる。

### 2. 統合レコードの作成

`Setup > Integration > Manage Integrations > New`

- **Token-Based Authentication** を有効化
- 作成後に表示される **Consumer Key / Consumer Secret** を控える

### 3. アクセストークンの作成

`Setup > Users/Roles > Access Tokens > New`

- 対象の統合レコード・ユーザー・ロールを選択
- 作成後に表示される **Token ID / Token Secret** を控える

> APIを使うユーザーのロールに **REST Web Services** の権限が必要。

---

## ローカル環境のセットアップ

### 依存パッケージのインストール

```bash
# macOS / Linux
pip3 install -r scripts/requirements.txt

# Windows
pip install -r scripts/requirements.txt
```

### `.env` ファイルの作成

`scripts/.env` を作成し、以下を設定：

```
NS_ACCOUNT_ID=1234567_SB1
NS_CONSUMER_KEY=xxxxx
NS_CONSUMER_SECRET=xxxxx
NS_TOKEN_ID=xxxxx
NS_TOKEN_SECRET=xxxxx
```

**Account IDの形式：**
- サンドボックス：`1234567_SB1`（`_SB` + 番号）
- 本番：`1234567`（数値のみ）

### 接続テスト

```bash
# macOS / Linux
python3 scripts/export_metadata_from_rest.py --test-auth

# Windows
python scripts/export_metadata_from_rest.py --test-auth
```

`認証成功` と表示されればOK。

---

## メタデータの取得（エクスポート）

### 特定レコードのみ取得（推奨）

```bash
# macOS / Linux
python3 scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item

# Windows
python scripts/export_metadata_from_rest.py --env SB --select salesorder,customer,item
```

### 全レコードを取得

```bash
python3 scripts/export_metadata_from_rest.py --env SB
```

> 全取得は時間がかかる。まずは必要なレコードに絞ることを推奨。

`--env` に指定した名前がそのまま出力フォルダ名になる（例：`SB` → `netsuite-metadata/SB/`）。

---

## メタデータの検索・活用

取得したメタデータは `query_metadata.py` で検索・活用できる。

### レコード一覧を確認

```bash
python3 scripts/query_metadata.py --env SB list-records
```

### レコードの詳細（全フィールド定義）を確認

```bash
python3 scripts/query_metadata.py --env SB get-record salesorder
```

### フィールド一覧を確認

```bash
python3 scripts/query_metadata.py --env SB list-fields salesorder
```

### 特定フィールドIDがどのレコードにあるか横断検索

```bash
python3 scripts/query_metadata.py --env SB find-field tranid
```

### SuiteQLクエリを自動生成

フィールド名を指定するだけで、対応するSuiteQL SELECT文を生成する。

```bash
python3 scripts/query_metadata.py --env SB suggest-suiteql salesorder --fields tranid,entity
```

出力例：
```json
{
  "environment": "SB",
  "record_key": "salesorder",
  "suiteql": "SELECT tranid, entity FROM transaction WHERE type = 'SalesOrd'"
}
```

> `transaction` テーブルに対して `WHERE type = 'SalesOrd'` のフィルタが自動で付与される点がポイント。SalesOrderのようにNetSuiteが内部でtransactionテーブルに統合しているレコードを正しく扱える。

---

## 出力データの構造

```
netsuite-metadata/
└── SB/
    ├── records/
    │   ├── salesorder.json   # フィールド定義（BYO形式）
    │   ├── customer.json
    │   └── ...
    ├── record_index.json     # レコード一覧インデックス
    └── manifest.json         # エクスポート情報（環境・日時等）
```

各 `records/*.json` の構造（抜粋）：

```json
{
  "record_key": "salesorder",
  "primary_table": {
    "suiteql_table": "transaction",
    "suiteql_type_filter": "SalesOrd"
  },
  "fields": {
    "tranid": {
      "label": "Document Number",
      "field_type": "text",
      "nullable": true,
      "suiteql_column": "tranid"
    },
    "entity": {
      "label": "Customer",
      "field_type": "record_ref",
      "ref": {
        "target_record_key": "customer",
        "relationship": "many_to_one"
      }
    }
  }
}
```

---

## 対応レコードタイプ（SuiteQLマッピング済み）

| REST record type | SuiteQL テーブル | type フィルタ |
|-----------------|-----------------|--------------|
| salesorder | transaction | SalesOrd |
| invoice | transaction | CustInvc |
| purchaseorder | transaction | PurchOrd |
| itemfulfillment | transaction | ItemFulfillment |
| customer | customer | — |
| vendor | vendor | — |
| item | item | — |
| employee | employee | — |
| subsidiary | subsidiary | — |
| account | account | — |
| customrecord_* | customrecord_* | — |

上記以外のカスタムレコードも `customrecord_` プレフィックスのものは自動で認識される。

---

## よくあるエラー

| エラー | 原因 | 対処 |
|--------|------|------|
| `HTTP 401` | 認証情報が間違っている・期限切れ | `.env` の値を確認。アクセストークンを再発行 |
| `環境変数 NS_ACCOUNT_ID が設定されていません` | `.env` が読み込まれていない | スクリプトと同じディレクトリに `.env` があるか確認 |
| `HTTP 403` | ロールに REST Web Services 権限がない | NetSuiteのロール設定を確認 |
| `Record 'xxx' not found in index` | メタデータ未取得 | `--select xxx` で先にエクスポートを実行 |
