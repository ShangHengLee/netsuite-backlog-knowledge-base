# NetSuite REST API によるメタデータ取得の仕組み
本文はMDファイルでこちらに保存しています。GitHubで読んだ方が少し見やすいかもしれません。↓
https://github.com/ShangHengLee/netsuite-backlog-knowledge-base/blob/main/backlogs/netsuite-rest-metadata/netsuite-rest-metadata.md

## 目次

1. [対象読者と前提知識](#対象読者と前提知識)
2. [概要](#概要)
3. [仕組みの全体像](#仕組みの全体像)
4. [認証：OAuth 1.0a Token-Based Authentication (TBA)](#認証oauth-10a-token-based-authentication-tba)
5. [NetSuiteでの事前設定](#netsuiteでの事前設定)
6. [ローカル環境のセットアップ](#ローカル環境のセットアップ)
7. [メタデータの取得（エクスポート）](#メタデータの取得エクスポート)
8. [メタデータの検索・活用](#メタデータの検索活用)
9. [出力データの構造](#出力データの構造)
10. [対応レコードタイプ（SuiteQLマッピング済み）](#対応レコードタイプsuiteqlマッピング済み)
11. [よくあるエラー](#よくあるエラー)
12. [⚠️ TBA廃止予定についての注意](#️-tba廃止予定についての注意)

---

## 対象読者と前提知識

| ロール | 活用シーン |
|--------|-----------|
| 開発者 | スクリプトを実行してメタデータをローカル保存し、開発・クエリ作成に活用 |
| コンサル | フィールド定義・構造の参照や、開発者への依頼時の仕様確認 |

スクリプトを自分で実行する場合は以下が必要です：

- **ターミナル（コマンドライン）の基本操作**
  - macOS: Terminal.app、Windows: コマンドプロンプトまたはPowerShell
  - コマンドを入力してEnterで実行する操作ができること
- **Python 3 のインストール**（[python.org](https://www.python.org/downloads/)）
  - macOS / Linux では `python3`、Windows では `python` コマンドを使用する
  - このドキュメントのコマンド例はどちらも併記しています
- **NetSuiteの認証情報（トークン）の理解**
  - このスクリプトはNetSuiteへの接続にOAuth 1.0aのTBA方式を使用する
  - Consumer Key / Consumer Secret / Token ID / Token Secret の4つが必要（詳細は[認証セクション](#認証oauth-10a-token-based-authentication-tba)を参照）
  - これらは通常、管理者が統合レコードとアクセストークンを作成することで発行される

コンサルの方でスクリプト実行が難しい場合は、開発者に依頼して出力ファイルを共有してもらうことも可能です。

---

## 概要

普段開発している時、レコードやフィールドのIDを調べたりするのに面倒くさいと思っているでしょう。
特にAIを使う時、間違ったコードを生成したりして、苦しく感じるときはよくあると思います。
そこで解決法ですが、
NetSuiteが提供するREST APIの **metadata-catalog** エンドポイントを使うことで、
SalesOrderやCustomerといった各レコードのフィールド定義（スキーマ情報）をローカルに取得・保存できる。

これにより以下のことが可能になる：

- レコードに存在するフィールド一覧の確認
- 各フィールドのデータ型・参照先レコードの確認
- **SuiteQLクエリの自動生成**（フィールド名を指定するだけでSELECT文を生成）
- AIツール（Claude等）への入力データとして活用

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

### `.env` ファイルの設定

`scripts/.env.example` をコピーして `scripts/.env` を作成し、各値を実際の認証情報に書き換えて使う：

```bash
cp scripts/.env.example scripts/.env
```

```
NS_ACCOUNT_ID=1234567_SB1
NS_CONSUMER_KEY=xxxxx
NS_CONSUMER_SECRET=xxxxx
NS_TOKEN_ID=xxxxx
NS_TOKEN_SECRET=xxxxx
```

**Account IDの確認方法・注意事項：**

`Setup > Company > Company Information` の **Account ID** フィールドに表示されている値をそのままコピーする。

> ⚠️ **大文字・小文字を含め、表示された値と完全に一致させること。**  
> 例えば `1234567_SB1` と `1234567_sb1` は別物として扱われ、認証エラーになる。

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

### Postman で動作確認する（推奨）

スクリプトを使う前に **Postman** で接続を確認しておくと、認証情報の問題かコードの問題かを切り分けやすくなる。

1. Postman で新規リクエストを作成
2. **Authorization** タブ → **OAuth 1.0** を選択
3. 以下を入力：

   | 項目 | 値 |
   |------|----|
   | Consumer Key | `NS_CONSUMER_KEY` の値 |
   | Consumer Secret | `NS_CONSUMER_SECRET` の値 |
   | Access Token | `NS_TOKEN_ID` の値 |
   | Token Secret | `NS_TOKEN_SECRET` の値 |
   | Signature Method | `HMAC-SHA256` |

4. URL に以下を入力して GET を送信：

   ```
   https://<ACCOUNT_ID>.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog/
   ```

   > `<ACCOUNT_ID>` は `.env` の `NS_ACCOUNT_ID` と同じ値（ただし小文字・ハイフン区切りに自動変換される場合あり。NetSuiteのドキュメントで確認すること）

5. `200 OK` が返れば認証成功。`401` の場合は認証情報を見直す。

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
| `HTTP 403` | ロールに REST Web Services 権限がない | NetSuiteのロール設定を確認、足りない権限を追加 |
| `Record 'xxx' not found in index` | メタデータ未取得 | `--select xxx` で先にエクスポートを実行 |

---

## ⚠️ TBA廃止予定についての注意

**NetSuiteはToken-Based Authentication (TBA / OAuth 1.0) を段階的に廃止する方針を公式に示している。**

### 廃止スケジュール

| 時期 | 内容 |
|------|------|
| **2026.1リリース（現在）** | 新規インテグレーションには OAuth 2.0 を推奨 |
| **2027.1リリース** | 新規インテグレーションでのTBA作成が**不可**になる（既存の動作は維持） |

> SuiteCloud SDK については廃止がより早く、**バージョン24.2（2024年8月）以降はOAuth 2.0のみ**をサポートし、TBA（OAuth 1.0）は削除済み。

### 対応方針

- **新規インテグレーション**：OAuth 2.0（Authorization Code Grant）を採用すること
- **既存のTBA実装**：2027.1までに OAuth 2.0 へ移行することを計画しておくこと（既存は即座に壊れないが、移行が必要）
