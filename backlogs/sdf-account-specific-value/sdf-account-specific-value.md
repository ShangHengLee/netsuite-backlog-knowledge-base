# NetSuite SDFでカスタムレコードのデータ移行時に [ACCOUNT_SPECIFIC_VALUE] になる

## 目次

1. [概要](#概要)
2. [原因](#原因)
3. [対処方法](#対処方法)
4. [注意点](#注意点)

---

## 概要

**SDFでカスタムレコードのデータを移行する際、勘定科目・場所などの標準レコードを参照するフィールドの値が `[ACCOUNT_SPECIFIC_VALUE]` になり、そのままでは移行できない。**

SDFは基本的にカスタムレコードの定義だけでなくレコードのデータまで移行できる。ただし、カスタムレコードの項目で標準レコード（勘定科目、場所など）を参照している場合は、XML上の値が `[ACCOUNT_SPECIFIC_VALUE]` となる。

対象読者：SDFで環境間（SB → 本番など）の移行を担当する開発者・コンサル

---

## 原因

標準レコードの内部IDは環境ごとに異なる。SDFは環境依存の値を移行先にそのまま持ち込めないため、`[ACCOUNT_SPECIFIC_VALUE]` というプレースホルダーに置き換えて出力する。

設定ミスや権限の問題ではなく、SDFの仕様である。

---

## 対処方法

REST APIやMCPを使って内部IDの対照表を作り、値を置換してから移行する。

1. 移行元・移行先の両環境で、対象レコードの内部IDを取得する（REST API の SuiteQL、または MCP の `ns_runCustomSuiteQL` など）
2. 勘定科目番号や場所名など、環境をまたいで一意になるキーで突き合わせ、「移行元の内部ID ⇄ 移行先の内部ID」の対照表を作る
3. 移行データ内の `[ACCOUNT_SPECIFIC_VALUE]` を、対照表をもとに**移行先の内部IDを数値で直書き**して置換する
4. 置換後のXMLを移行先にデプロイする

### XMLの置換前後の例

カスタムレコード `customrecord_sw_if_glass_location`（Glass場所変換マスタ）の1行。`custrecord_sw_igl_location_transfer`（海外輸送中）と `custrecord_sw_igl_location_inspection`（検品前）は、標準レコード「場所」を参照するフィールドである。

**置換前**（`object:update --includeinstances` で取得した直後）

```xml
<instance scriptid="val_igl_001A">
  <custrecord_sw_igl_location_from>001A</custrecord_sw_igl_location_from>
  <custrecord_sw_igl_location_inspection>[ACCOUNT_SPECIFIC_VALUE]</custrecord_sw_igl_location_inspection>
  <custrecord_sw_igl_location_transfer>[ACCOUNT_SPECIFIC_VALUE]</custrecord_sw_igl_location_transfer>
  <isinactive>F</isinactive>
</instance>
```

**置換後**（移行先環境の場所の内部IDを直書き。以下は検品前=9410、海外輸送中=9417の例）

```xml
<instance scriptid="val_igl_001A">
  <custrecord_sw_igl_location_from>001A</custrecord_sw_igl_location_from>
  <custrecord_sw_igl_location_inspection>9410</custrecord_sw_igl_location_inspection>
  <custrecord_sw_igl_location_transfer>9417</custrecord_sw_igl_location_transfer>
  <isinactive>F</isinactive>
</instance>
```

複数選択フィールドの場合、置換前は `[ACCOUNT_SPECIFIC_VALUE]|[ACCOUNT_SPECIFIC_VALUE]` のように `|` 区切りで出力される。置換後も内部IDを `|` 区切りで並べる（例: `4|12`）。

---

## 注意点

- 突き合わせキーは、変更されにくいコード類（勘定科目番号など）を優先する。
- 移行先に該当する標準レコードが存在しない場合は、先にマスタを整備してから移行する。
- `project:validate --server` や `project:deploy --dryrun` は、内部IDが実在するかを検証しない。検証が通っても正しいとは限らないため、デプロイ後にUIで目視確認する。
- 移行元から再取得すると `[ACCOUNT_SPECIFIC_VALUE]` に戻る。再取得のたびに対照表で置換し直す。
- カスタムリストの値や、他のカスタムレコードの行を参照するフィールドは、内部IDではなく `[scriptid=customlist_xxx.val_...]` 形式で書く（内部IDだと検証で拒否される）。内部IDの直書きが必要なのは、場所・従業員などの標準レコード参照。
- 勘定科目・場所以外でも、環境ごとに内部IDが異なる標準レコードを参照している項目は同様に対象となりうる。移行前に対象のカスタムレコードと参照フィールドを洗い出しておく。
