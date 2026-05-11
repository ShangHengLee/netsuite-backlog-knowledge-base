# SuiteCloud Developer Assistant セットアップガイド

## 概要

SuiteCloud Developer Assistant は、NetSuite の開発環境に接続した AI コーディングアシスタントです。VS Code の SuiteCloud Extension と Cline 拡張機能を組み合わせることで、NetSuite スキーマを参照しながらの SuiteScript 開発が可能になります。

想定読者：SuiteScript 開発者（VS Code 利用者）

---

## 前提条件

- **VS Code**（スタンドアロン版。Cursor では動作しない）
- **SuiteCloud Extension for VS Code**（Oracle 公式）
- **Cline Extension**（VS Code マーケットプレイスから入手）
- **Auth ID**（SuiteCloud CLI でセットアップ済みの認証 ID）

Auth ID の確認方法：

```bash
suitecloud account:manageauth --list
```

---

## セットアップ手順

### 1. SuiteCloud Extension の設定

VS Code の設定（`Ctrl+,`）を開き、**Workspace > Extensions > SuiteCloud** に移動する。

| 項目 | 設定値 |
|------|--------|
| Developer Assistant: Auth ID | 使用する Auth ID（例：`jkc_sb`） |
| Developer Assistant: Local Port | デフォルトのまま（競合なければ変更不要） |
| Developer Assistant: Enable | ✓ チェックを入れる |

有効化すると **API Key** と **Base URL** がポップアップ表示される。両方をコピーして保存する。

### 2. Cline の設定

Cline 拡張機能の設定 → **Edit in settings** を開き、以下を入力する。

| 項目 | 設定値 |
|------|--------|
| API Provider | `OpenAI Compatible` |
| API Key | 手順 1 でコピーした API Key |
| Base URL | 手順 1 でコピーした Base URL |
| Model ID | `NetSuite` |

Model Configuration セクションで：
- `Supports Images` → **チェックを外す**（NetSuite モデルは画像非対応）
- Context Window Size → `1,000,000`

---

## 仕組み

```
SuiteCloud Extension（VS Code）
  → Auth ID を使いローカルサーバーを起動
  → API Key と Base URL を発行
        ↓
Cline → Base URL 経由で自動接続
        ↓
Oracle/NetSuite 専用 LLM（OpenAI 互換プロトコル）
```

接続先の NetSuite 環境は Auth ID に紐づいた環境（SB/PROD など）が自動的に使われる。手動でのリンク操作は不要。

---

## できること

| 機能 | 内容 |
|------|------|
| SuiteScript コード生成 | NetSuite スキーマを参照した上でコードを生成 |
| XML カスタムオブジェクト作成 | SDF 用 XML ファイルの生成と manifest.xml の更新 |
| ユニットテスト生成 | モック込みのテストコードを自動作成 |
| コード補完・最適化 | import 提案、重複除去、リネーム提案 |
| ドキュメント生成 | README、コードコメントの自動作成 |

使用モデルは **Oracle/NetSuite 独自 LLM**。OpenAI や Anthropic には送信されない。

---

## 落とし穴・注意事項

**Cursor では動作しない**
Cursor は VS Code ベースだが SuiteCloud Extension に対応していない。スタンドアロンの VS Code が必要。

**NetSuite への直接クエリはできない**
「利用可能なカスタムレコード一覧を教えて」のような質問に対し、Cline が Suitelet を作成してデプロイしようとする場合がある。環境に関する調査系の質問は避け、具体的な開発タスクを投げること。

```
---

## 参考

- [SuiteCloud Developer Assistant セットアップ（Oracle 公式）](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/subsect_1121114206.html)
- [Capabilities and Supported Tasks（Oracle 公式）](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_1124055714.html)
