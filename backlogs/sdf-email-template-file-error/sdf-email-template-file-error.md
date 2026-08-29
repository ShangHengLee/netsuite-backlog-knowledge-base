# SDFでメールテンプレートをデプロイすると「Provide a non-empty template file...」が出る

## 概要

対象前提：SDFの基本操作が慣れている方
SDF（SuiteCloud Development Framework）でメールテンプレート関連のファイルをデプロイまたは検証した際に、以下のようなエラーが発生することがあります。

```text
Provide a non-empty template file...
```

このエラーは、メールテンプレートの定義ファイルと実体ファイルが正しくペアになっていない、またはデプロイ対象として認識されていない場合に発生しやすいです。

特に NetSuiteのFile Cabinet 上で管理されるメールテンプレートは、単一ファイルではなく、XMLとHTMLの2つのファイル構成で扱われる仕様があるため、SDF の対象指定に注意が必要です。

---

## 対象の事象

SDF でプロジェクトのデプロイやバリデーションを実行したとき、以下のような状態で失敗することがあります。

- `deploy.xml` で対象ファイルやフォルダを指定している
- メールテンプレートの XML 定義ファイルだけが対象になっている
- HTML 本文ファイルがデプロイ対象から漏れている
- フォルダ指定が `/*` になっていない (←未だに謎)

このようなケースでは、SDF が「テンプレートの内容が空」または「正しく認識できない」と判断して、`Provide a non-empty template file...` というエラーを出します。

---

## NetSuite の仕様：メールテンプレートは XML + HTML（または FTL）のペア

NetSuite のメールテンプレートは、File Cabinet 上で以下のような構成で管理されることが多いです。

```text
FileCabinet/
└── SuiteScripts/
    └── Templates/
        └── EmailTemplates/
            ├── notification_template.xml
            └── notification_template.html
```

メールテンプレートは「XML だけ」で完結するものではなく、実体ファイル（HTML ）とセットで扱う必要があります。

1. XMLファイル
   - テンプレートのメタデータ定義
   - ファイル名、説明、格納先、アクセス権などが含まれる
   - SDF ではこの XML が「定義ファイル」として扱われる

2. HTMLファイル
   - 実際のメール本文
   - テンプレートの本文ソースが入る
   - XML だけでは本文が存在しないため、SDF が正しく認識できないことがある

---

## 原因の整理

このエラーが発生する典型パターンは、次のどれかです。

### パターン1: XML ファイルだけを指定している

```xml
<path>~/FileCabinet/SuiteScripts/Templates/EmailTemplates/notification_template.xml</path>
```

このように個別ファイルを指定した場合、対応する HTML ファイルが含まれず、SDF がテンプレートとして不完全だと判定することがあります。

### パターン2: フォルダ指定が不十分

```xml
<path>~/FileCabinet/SuiteScripts/Templates/EmailTemplates</path>
```

フォルダを指定していても、`/*` を付けていない場合、SDF がフォルダ配下のすべてのファイルを再帰的に対象にしてくれないことがあります。

### パターン3: XML と HTML の両方がプロジェクトに含まれていない

既存環境から `project:import` や `object:import` で取り出した際に、XML だけが取り込まれていたり、HTML 側が別のフォルダに置かれていたりすると、SDF の認識がズレます。

---

## 解決策：対象フォルダを `/*` で指定する

最も確実なのは、メールテンプレートの格納先フォルダを対象とし、末尾に `/*` を付けて、フォルダ内のすべての関連ファイルをデプロイ対象に含める方法です。

> 重要なポイントは、対象を実名指定ではなく「フォルダ配下全体」にして `/*` を付けることです。

---

## 実際の `deploy.xml` の書き方

以下のような形で設定すると、メールテンプレート群をまとめて対象にできます。

```xml
<files>
  <path>~/FileCabinet/SuiteScripts/Templates/EmailTemplates/*</path>
</files>
```

また、もし明示的に複数のファイルを管理したい場合でも、テンプレートの XML と HTML の両方が対象に含まれているかを確認してから実行します。

## まとめ

SDF でメールテンプレートのデプロイ時に `Provide a non-empty template file...` が発生した場合、ほぼ間違いなく「XML 定義ファイルだけが対象になっていて、HTMLの実体ファイルが未認識」または「フォルダ指定が `/*` になっていない」ことが原因です(根本原因は不明ですが)。

NetSuiteのメールテンプレートは、XMLとHTMLのペアで管理される仕様であるため、デプロイ対象を以下のように設計するのが安全です。

```xml
<path>~/FileCabinet/SuiteScripts/Templates/EmailTemplates/*</path>
```