# NetSuiteのIPアドレス制限仕様とSWJ側のIPアドレス回避策

## 概要

対象前提：ロールの権限設計・アカウントセキュリティ設定に関わる管理者

JKCで2要素認証ではなく、IPによるログイン制御がしたいという要望があったため、
研究してわかった仕様をまとめます。

NetSuiteの「IPアドレス制限（IP Address Rules）」は、ログインを許可するIPアドレスをNetSuite上で制御する機能。名前付きの単一「ルールレコード」があるわけではなく、以下3つの設定レイヤーの組み合わせで動作する。

1. **会社レベル**：会社情報（Company Information）の「許可IPアドレス（Allowed IP Addresses）」フィールド
2. **従業員レベル**：各従業員レコードの「アクセス（Access）」サブタブにある「会社からIPルールを継承（Inherit IP Rules from Company）」チェックボックスと「IPアドレス制限（IP Address Restriction）」フィールド
3. **ロールレベル**：ロールレコードの「このロールをIPアドレスで制限する（Restrict this role by IP Address）」チェックボックス（このロールにIP制限を適用するかどうかのスイッチ）

IP制限を有効化した際にSWJ側のアカウントがロックアウトされないようにする方法（本記事の本題）は、従業員レコードの「IPアドレス制限（IP Address Restriction）」フィールドに文字列 `ALL` を入力すること（詳細・適用範囲は後述）。

---

## まずは機能の有効化

設定（Setup） > 会社（Company） > 機能の有効化（Enable Features）の「会社（Company）」サブタブ、「アクセス（Access）」セクションにある「IPアドレスのルール（IP Address Rules）」のチェックボックスをオンにして保存する（出典：[Enable the IP Address Rules Feature](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1535043532.html)）。

注意点として、この機能を有効化しても、**有効化以前から存在するカスタムロール**には自動的にIP制限が適用されない（後述のロールレベル設定を参照）。

---

## 設定方法

### 1. 会社レベル（Company Information）

設定（Setup） > 会社（Company） > 会社情報（Company Information）の「許可IPアドレス（Allowed IP Addresses）」フィールドに、アカウント全体で許可するIPv4アドレスをカンマまたはスペース区切りで入力する（出典：[Enabling and Creating IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_4726612641.html)）。
空欄は受容しません。

#image(pasted-2026.08.30-01.03.08.png)

### 2. 従業員レベル（Employee レコード）

リスト（Lists） > 従業員（Employees） > 従業員（Employees）から対象の従業員を編集し、「アクセス（Access）」サブタブを開く。

- 「会社からIPルールを継承（Inherit IP Rules from Company）」：チェックすると会社レベルのIPアドレスを継承する
- 「IPアドレス制限（IP Address Restriction）」：この従業員個別のIPアドレス制限を入力するフィールド

「IPアドレス制限（IP Address Restriction）」フィールドに指定できる書式（出典：[Create Individual IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1535041428.html)）：

| 書式 | 例 |
|---|---|
| 単一IP | `123.45.67.89` |
| 範囲（ハイフン） | `123.45.67.80-99` または `123.45.67.80-123.45.67.99` |
| 複数IP（スペース/カンマ区切り） | `123.45.67.90, 123.45.67.97` |
| ネットマスク形式 | `123.45.67.80/255.255.255.0` |
| CIDR形式 | `123.45.67.80/24` |
| 全拒否 | `NONE` |
| 全許可 | `ALL` |
| 空欄 | 会社レベルの設定を継承 |

文字数上限は4,000文字。

チェックボックスとフィールドの組み合わせによる挙動：

- **チェックON＋フィールドに個別IPを入力**：会社レベルのIP **と** 個別入力したIPの **両方** からアクセス可能（加算）
- **チェックOFF＋フィールドに入力あり**：入力したIPアドレス **のみ** アクセス可能（会社レベルは無視）
- **チェックOFF＋フィールド空欄**：結局、会社レベルの設定が適用される
#image(pasted-2026.08.30-01.03.47.png)

### 3. ロールレベル（ロールレコード）

設定（Setup） > ユーザー/ロール（Users/Roles） > ロールの管理（Manage Roles）で対象ロールの「カスタマイズ（Customize）」を開き、「このロールをIPアドレスで制限する（Restrict this role by IP Address）」チェックボックスを操作する（出典：[Restricting a Role by IP Address](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/bridgehead_N288693.html)）。

- チェックON：このロールでのログインは、（会社／従業員レベルで決まる）許可IPアドレスからのみ可能
- チェックOFF：このロールにはIPアドレス制限が適用されない（＝誰がこのロールでログインしてもIPチェックを受けない）
#image(pasted-2026.08.30-01.04.48.png)
---

## 制限の評価タイミングと対象外の経路

Oracle公式ドキュメント（[Enabling and Creating IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_4726612641.html)）による記載：

- **「IP Address Rules are effective after successful login. The rules don't replace a password reset or the login flow.」**：IPアドレス制限は認証（パスワード等）の代替ではなく、ログイン成功後に効く追加のアクセス制御という位置付け。
- SOAP Web Services、SAML SSO、OpenID Connect SSO はIPアドレス制限の対象になる(例えばDataSpider)
- **SuiteAnalytics Connect はIPアドレス制限の対象外**（制限に関係なくアクセスできる）
- IPv4のみサポート。IPv6は非対応
- Oracle自身が、IPアドレスはなりすまし（spoofing）が可能でクライアントに固定されないケースも多いことを理由に、**IPアドレス制限より二要素認証（2FA）を優先して検討すること**を推奨している

---

## SWJ側、保守用アカウントのロックアウト回避方法（従業員レコード側でALL設定）

「IP制限を設定したせいで、保守・運用側のアカウントが締め出される」事故を防ぐ方法は、Oracle公式ドキュメント上に明記されている。結論：

> 従業員レコード（リスト（Lists） > 従業員（Employees） > 従業員（Employees））の「アクセス（Access）」サブタブにある「IPアドレス制限（IP Address Restriction）」フィールドに、文字列 **`ALL`** を入力する。

これにより、その従業員は（そのフィールドの意味が「全IPアドレスを許可」であるため）IPアドレス制限の対象外になる。出典は上記の[Create Individual IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1535041428.html)ページにある「ALL」の説明で、これはOracle一次資料上の記述であり信頼度は高い。

**この設定はSWJ（実装・保守担当）側のアカウントに限定する。** クライアント（管理者含む）には例外を設けず、会社／ロールレベルの制限をそのまま適用する。ロールレコード側の「このロールをIPアドレスで制限する（Restrict this role by IP Address）」を外せば全ユーザー一括で対象外にすることも可能だが、粒度が粗いため今回の用途（SWJアカウントのみの個別例外化）には従業員レコードの `ALL` 設定の方が適する。

---

## 実務上の注意点

- 動的IPアドレス（自宅回線等）を使う従業員が多い環境では、IPアドレス制限は運用負荷が高くなりやすい。Oracle自身も2FAを優先的な代替策として案内している
- SuiteAnalytics ConnectはIPアドレス制限の対象外である点に注意（BIツール等の連携用アカウントには効かない）

---

## まとめ

- IPアドレス制限は**会社／従業員／ロール**の3層構成。単一の「ルールレコード」はない
- 機能の有効化：設定（Setup） > 会社（Company） > 機能の有効化（Enable Features） > 「会社（Company）」サブタブ > 「アクセス（Access）」セクションの「IPアドレスのルール（IP Address Rules）」
- 従業員レコードの「IPアドレス制限（IP Address Restriction）」に `ALL` を入力すると、その従業員はIP制限の対象外になる（Oracle公式に明記、信頼度高）。**SWJ側アカウント専用の運用であり、クライアントには適用しない**
- IPアドレス制限はログイン成功後に効く追加チェックであり、パスワード認証等の代替にはならない。SuiteAnalytics Connectは対象外
- ロール制限とEmployeeのALL設定の優先順位はOracle公式では未確認。本番適用前に実機検証を推奨

---

## 参考資料

- [NetSuite Applications Suite - Enabling and Creating IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_4726612641.html)
- [NetSuite Applications Suite - Enable the IP Address Rules Feature](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1535043532.html)
- [NetSuite Applications Suite - Create Individual IP Address Rules](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1535041428.html)（従業員レコードの `ALL` / `NONE` の記載元）
- [NetSuite Applications Suite - Restricting a Role by IP Address](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/bridgehead_N288693.html)
- [IP Address Rules in NetSuite | SuiteRep（二次情報源）](https://suiterep.com/2023/08/07/ip-address-rules-in-netsuite/)
- [How to Set Up IP Address Restrictions in NetSuite（二次情報源）](https://www.anchorgroup.tech/blog/how-to-set-up-ip-address-restrictions-in-netsuite-erp-security)
