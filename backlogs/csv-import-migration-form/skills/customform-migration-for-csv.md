# 移行用カスタムフォーム作成スキル（CSVマッピング対応）

## 目的
- 環境に存在する元フォーム（`env`）から、移行用フォーム（`iko`）を作成する。
- CSVインポートでフィールドをマッピング可能にするため、**元の `visible=T` の項目を対象に `displayType=NORMAL` にする**。
- その後、dry-run でエラーになった標準フィールドのみ、アカウント現状に合わせて戻す。

## 適用範囲（必須）
- このカテゴリの作業（移行用フォーム作成・修正・デプロイ）では、着手前に本手順を必ず読む。

## 手順

### 1) NetSuite から元フォームを取得
- 必要なら `suitecloud object:import` で対象のカスタムフォームを取り込む。
- 既に `src/Objects/env/customform/` にある場合はそれを元として使う。

### 2) 移行用フォルダへコピーして命名
- `src/Objects/env/customform/<base>.xml` を
  `src/Objects/iko/customform/<iko_name>.xml` にコピーする。
- 例:
  - `custform_sw_rental_sales.xml`
  - `custform_sw_iko_rental_sales.xml`
- ルート要素の `scriptid` と `<name>` を移行用名称に更新する。

### 3) フィールドを通常化（NORMAL）
- 原則: **元フォームで `visible=T` の項目のみ** を対象に、`displayType=NORMAL` にする（標準/カスタム共通）。
- `mandatory` についても一旦元ファイルから変更して問題ないが、dry-run で変更不可エラーが出た項目のみ戻す。
- 移行用XML作成後は、置換対象に `<preferred>` も含め、`<preferred>T</preferred>` は `<preferred>F</preferred>` に変更する。
- 注意:
  - `visible=F` の項目は、この手順では `displayType` を変更しない。
  - 標準フィールドは変更不可なことがある（`mandatory` / `displayType` など）。
  - 変更不可エラーが出たフィールドだけを最小限で戻す（先回りで戻さない）。

### 4) `deploy.xml` に追加
- `src/deploy.xml` の `<objects>` に移行用フォームを追加する。
- 例:
  - `~/Objects/iko/customform/custform_sw_iko_rental_sales.xml`

### 5) 依存関係を `manifest.xml` に追加
- まず自動追加を試す:
  - `suitecloud project:adddependencies`
- 必ず差分を確認し、不要な副作用（feature の required 化など）があれば修正する。
  - 例: `REVENUERECOGNITION` が `required="true"` に変わり、環境未有効で失敗するケース。

### 6) Dry-run を実行し、エラーがなくなるまで修正
- 実行:
  - `suitecloud project:deploy --dryrun`
- 修正優先順位:
  1. **依存関係エラー**: フィールド削除の前に `manifest.xml` 追加を優先（自動追加 + 手動調整）。
  2. **変更不可エラー**: エラーになった標準フィールドの該当属性だけを戻す（例: mandatory を削除/復元、displayType を元に戻す）。
  3. **最終手段**: プロジェクトに存在しない参照で、依存追加でも解決しない場合のみ参照削除を検討。

### 7) 本番デプロイ前にユーザー確認
- dry-run 成功後、必ずユーザーに確認:
  - `suitecloud project:deploy` を実行してよいか。

## チェックリスト
- [ ] 元フォームは `env` 側を基準にしたか
- [ ] `iko` 側の `scriptid` / `<name>` を更新したか
- [ ] 元の `visible=T` 項目のみ `NORMAL` 化したか（標準/カスタム）
- [ ] `<preferred>T</preferred>` を `<preferred>F</preferred>` に変更したか
- [ ] `deploy.xml` に追加したか
- [ ] `project:adddependencies` を実行したか
- [ ] `manifest.xml` の副作用差分を確認したか
- [ ] `project:deploy --dryrun` がエラーゼロか
- [ ] 本番 `project:deploy` 前にユーザー確認したか
