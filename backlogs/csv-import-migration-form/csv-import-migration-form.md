# NetSuite CSVインポートによるデータ移行：移行専用フォームの考え方

## 目次

1. [対象読者と前提知識](#対象読者と前提知識)
2. [概要](#概要)
3. [背景：CSVインポートとフィールド表示の制約](#背景csvインポートとフィールド表示の制約)
4. [解決アプローチの全体像](#解決アプローチの全体像)
5. [前提条件・必要なツール](#前提条件必要なツール)
6. [SDFプロジェクトのセットアップ](#sdfプロジェクトのセットアップ)
7. [元フォームのダウンロード](#元フォームのダウンロード)
8. [移行用フォームの作成](#移行用フォームの作成)
9. [SDFでのデプロイ](#sdfでのデプロイ)
10. [CSVインポートの設定](#csvインポートの設定)
11. [AIによる自動化（スキル活用）](#aiによる自動化スキル活用)
12. [よくあるエラーと対処](#よくあるエラーと対処)

---

## 対象読者と前提知識

| ロール | 活用シーン |
|--------|-----------|
| 開発者 | SDF操作・フォームXML編集・デプロイを担当する |
| コンサル | データ移行プロジェクトでCSVインポートの設計を行う |
| 管理者 | 移行作業の承認・NetSuite側の設定（フォーム適用など）を担当する |

この手順を実施するには以下の知識が必要です：

- **SuiteCloud Development Framework (SDF) の基本操作**
  - `suitecloud` CLIがローカルにインストールされていること
  - `project:deploy` / `object:import` コマンドの実行経験
- **NetSuiteのカスタムフォームの概念**
  - フォームのフィールド表示設定（displayType / visible）の理解
- **XMLの基本的な読み書き**
  - フォームオブジェクトはXML形式で管理される

---

## 概要

NetSuiteのCSVインポートは強力なデータ移行機能だが、**フォーム上でインライン（inline）または非表示（hidden）になっているフィールドはマッピング対象に表示されない**という制約がある。

この問題を回避するため、一つの考えとして、以下のアプローチを採用する：

1. SDFで既存フォームをダウンロードする
2. フィールドの `displayType` を `NORMAL` に書き換えた**移行専用フォーム**を作成する
3. SDF経由でNetSuiteにデプロイする
4. その移行専用フォームを使ってCSVインポートを設定する

この一連の作業は繰り返し発生するため、**AIスキル（CLAUDE.mdへの登録）** として定義することで、次回以降はAIに手順を実行させて効率化できる。

---

## 背景：CSVインポートとフィールド表示の制約

### なぜフィールドがマッピングできないのか

NetSuiteのCSVインポートウィザードは、**レコードに紐づくフォームの表示設定**を参照している。フィールドの `displayType` が以下の値の場合、CSVインポートのフィールドマッピング画面に表示されない：

| displayType | 意味 | CSVマッピング |
|-------------|------|--------------|
| `NORMAL` | 通常表示 | 表示される |
| `INLINE` | インライン表示（編集不可） | **表示されない** |
| `HIDDEN` | 非表示 | **表示されない** |
| `DISABLED` | 無効（読み取り専用） | **表示されない** |

業務フォームでは、参照用・自動計算用のフィールドをINLINEやHIDDENにすることが多い。しかしデータ移行時にはそれらのフィールドにも値を入力したいケースが頻繁に発生する。

### 標準フォームを直接変更できない理由

NetSuiteの標準フォームやすでに運用中のカスタムフォームを直接変更すると、業務画面のレイアウトに影響する。また、標準フォームはSDF経由での変更が制限されている。

そのため、**移行専用のフォームを別途作成**するアプローチが安全かつ実用的である。

---

## 解決アプローチの全体像

```
NetSuite 環境
  └── 既存のカスタムフォーム（env）
          │
          │  suitecloud object:import
          │
          ↓
  ローカル SDF プロジェクト
  src/Objects/env/customform/<base>.xml
          │
          │  XMLをコピー・編集
          │  visible=T の項目を displayType=NORMAL に変更
          │
          ↓
  src/Objects/iko/customform/<iko_name>.xml
          │
          │  suitecloud project:deploy --dryrun
          │  suitecloud project:deploy
          │
          ↓
  NetSuite 環境
  └── 移行専用フォーム（iko）がデプロイ済み
          │
          ↓
  CSVインポート設定
  └── 移行専用フォームを選択
  └── 全フィールドがマッピング可能な状態
```

---

## 前提条件・必要なツール

### SuiteCloud CLI のインストール

```bash
npm install -g @oracle/suitecloud-cli
```

### SDF アカウント設定

```bash
suitecloud account:setup
```

対話形式で Account ID・ユーザー情報を入力する。サンドボックスと本番で別々のアカウント設定が必要。

### 必要なNetSuite権限

| 権限 | 説明 |
|------|------|
| SuiteCloud Development | SDF オブジェクトの import/deploy |
| Custom Forms | カスタムフォームの編集 |
| CSV Import | CSVインポートの作成・実行 |

---

## SDFプロジェクトのセットアップ

### 新規プロジェクト作成（既存プロジェクトがない場合）

```bash
suitecloud project:create
```

プロジェクトタイプは `ACCOUNTCUSTOMIZATION` を選択する。

### フォルダ構成

移行用フォームは `iko` ディレクトリに分けて管理することを推奨する：

```
src/
├── Objects/
│   ├── env/
│   │   └── customform/
│   │       └── custform_<record>.xml     # 元フォーム（参照用）
│   └── iko/
│       └── customform/
│           └── custform_iko_<record>.xml  # 移行専用フォーム
├── deploy.xml
└── manifest.xml
```

---

## 元フォームのダウンロード

### 対象フォームのスクリプトIDを確認

NetSuiteの `Customization > Forms > Entry Forms（または Transaction Forms）` から対象フォームの **Script ID** を確認する。

### SDFでインポート

```bash
suitecloud object:import \
  --destinationfolder src/Objects/env/customform \
  --type customtransactionform \
  --scriptid custform_<scriptid>
```

> `customtransactionform`（取引フォーム）または `customentryform`（エントリーフォーム）のどちらかを指定する。

---

## 移行用フォームの作成

### 1. XMLファイルをコピー

```bash
cp src/Objects/env/customform/custform_<base>.xml \
   src/Objects/iko/customform/custform_iko_<base>.xml
```

### 2. scriptid と name を変更

コピーしたXMLのルート要素を編集する：

```xml
<!-- 変更前 -->
<customtransactionform scriptid="custform_sw_rental_sales">
  <name>レンタル売上フォーム</name>

<!-- 変更後 -->
<customtransactionform scriptid="custform_sw_iko_rental_sales">
  <name>【移行用】レンタル売上フォーム</name>
```

### 3. フィールドを NORMAL 化

**`visible=T` のフィールドのみ**を対象に `displayType` を `NORMAL` に変更する。

エディタの一括置換では対応しきれないため、以下の判断基準で手動またはAIに変更させる：

- `<visible>T</visible>` を含むフィールド → `displayType` を `NORMAL` に変更
- `<visible>F</visible>` を含むフィールド → **変更しない**

また、`<preferred>T</preferred>` を `<preferred>F</preferred>` に変更する（移行フォームをデフォルトフォームにしないため）。

### AIを使った変換

この変換作業はAIに依頼すると効率的。`skills/customform-migration-for-csv.md` をAIのコンテキストに渡した上で指示する：

```
以下のスキルに従って、元フォームから移行用フォームを作成してください。
スキル: [skills/customform-migration-for-csv.md の内容]
元フォーム: [src/Objects/env/customform/custform_<base>.xml の内容]
```

---

## SDFでのデプロイ

### deploy.xml に追加

```xml
<deploy>
  <configuration>
    <path>~/AccountConfiguration/*</path>
  </configuration>
  <objects>
    <path>~/Objects/iko/customform/custform_iko_<base>.xml</path>
  </objects>
</deploy>
```

### 依存関係の自動追加

```bash
suitecloud project:adddependencies
```

実行後、`manifest.xml` の差分を確認する。`REVENUERECOGNITION` など環境で有効でないfeatureが `required="true"` になっていた場合は手動で削除する。

### Dry-run でバリデーション

```bash
suitecloud project:deploy --dryrun
```

エラーが出た場合の対処：

| エラー種別 | 対処方法 |
|-----------|---------|
| 依存関係エラー | `manifest.xml` に不足しているオブジェクトを追加 |
| 変更不可エラー（標準フィールド） | エラーになった属性のみ元の値に戻す |
| 参照先オブジェクト不在 | `manifest.xml` への追加 → 解決しない場合のみ参照を削除 |

### 本番デプロイ

dry-run でエラーがゼロになったことを確認してからデプロイする：

```bash
suitecloud project:deploy
```

> **必ずユーザーに確認してからデプロイすること。** 本番環境への影響があるため。

---

## CSVインポートの設定

### 移行専用フォームの適用

1. `Setup > Import/Export > Import CSV Records` に移動
2. インポートタイプを選択（例：Transactions > Sales Orders）
3. CSVファイルをアップロード
4. **Advanced Options** または **Form** の項目で、デプロイした移行専用フォーム（`【移行用】〜`）を選択
5. フィールドマッピング画面で、`displayType=NORMAL` に変更したフィールドが表示されていることを確認

### マッピング後の保存

設定が完了したら **Save & Run** または **Save** でCSVインポートテンプレートとして保存しておくと、次回以降の再利用が容易になる。

---

## AIによる自動化（スキル活用）

### スキルの目的

`skills/customform-migration-for-csv.md` は、この一連の作業手順をAIが正確に実行できるよう定義した**スキルファイル**である。

Claude CodeなどのAIエージェントを使う際に、このスキルファイルを `CLAUDE.md` から参照させることで、AIが手順を理解した上で作業を進める。

### CLAUDE.md への登録例

SDFプロジェクトの `CLAUDE.md` に以下を追記する：

```markdown
## 必須スキル（移行用カスタムフォーム）

- 移行用フォーム作成（`env` から `iko` を作成し、CSVマッピング可能な状態にする作業）では、必ず以下を事前確認する:
  - `skills/customform-migration-for-csv.md`
- このカテゴリの作業は、実装・デプロイ前に上記手順の遵守を必須とする。
```

### AIへの指示例

```
custform_sw_salesorder を元に移行用フォームを作成してください。
スキル（skills/customform-migration-for-csv.md）の手順に従い、
dry-run がエラーゼロになるまで修正したうえで、
デプロイ前に確認を取ってください。
```

AIはスキルの手順に従い、以下を自動で行う：

1. 元フォームXMLを読み込む
2. `visible=T` のフィールドを `displayType=NORMAL` に変更
3. `<preferred>T</preferred>` を `<preferred>F</preferred>` に変更
4. `scriptid` と `<name>` を移行用に更新
5. `deploy.xml` と `manifest.xml` を更新
6. `--dryrun` を実行してエラーを修正
7. ユーザー確認後にデプロイ

---

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| CSVマッピング画面にフィールドが出ない | `displayType` が `NORMAL` 以外のまま | フォームXMLを確認し、再デプロイ |
| `deploy --dryrun` で「変更不可」エラー | 標準フィールドの `mandatory` や `displayType` を変更しようとしている | エラーになった属性のみ元の値に戻す |
| `deploy --dryrun` で依存関係エラー | `manifest.xml` に参照先オブジェクトが未登録 | `project:adddependencies` を実行、または手動で追加 |
| フォームをデプロイしても画面に表示されない | `<preferred>T</preferred>` のままでデプロイした | `preferred` を `F` に変更して再デプロイ、または画面のフォームセレクタから選択 |
| `suitecloud object:import` でフォームが見つからない | scriptid が間違っている | NetSuiteのフォーム設定画面でスクリプトIDを再確認 |
