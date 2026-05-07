# NetSuite 週次テックレポート — 2026-05-07

> 対象期間: 2026年2月〜5月  
> 主要リリース: NetSuite 2026.1（本番適用: 2026年2月〜4月）

---

## 更新情報・リリースノート

### NetSuite 2026.1 リリースノート（公式）
- 2026年2月から本番アカウントへの自動適用が開始、4月末に完了
- Oracle 社内では「NetSuite Next」構想と連動した近年最大規模のリリースと位置付け
- Evan Goldberg（共同創業者）は「会社設立以来最大のアップデート」と表現
- 出典: [Oracle NetSuite 2026.1 Release Notes](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_N3944673.html)

### NetSuite 2026.1 開発者・ITアーキテクト向け変更点（BrokenRubik）
- SuiteScript、REST API、SuiteCloud 全域にわたる技術的変更を網羅
- SOAP から REST への移行ロードマップが明確化
- 出典: [BrokenRubik — NetSuite 2026.1 Developers & IT Architects](https://www.brokenrubik.com/blog/netsuite-2026-1-release-notes-developers-it-architects)

---

## SuiteScript 更新

### SuiteScript 2.1 新機能（2026.1）
- **N/ai モジュール追加**: サーバーサイドスクリプトから SuiteCloud AI 機能へ直接アクセス可能に
  - `ai.classify()`, `ai.extract()`, `ai.summarize()`, `ai.generate()` の4メソッドを提供
- **async/await ネイティブ対応**: Map/Reduce スクリプトおよび Scheduled スクリプトで `async/await` が利用可能に。コールバックチェーンが解消され、`try/catch` による例外処理が簡潔になる
- **クエリモジュールの CTE サポート**: `N/query` モジュールが Common Table Expressions（CTE）に対応。複雑な分析クエリの可読性が向上し、サブクエリのパフォーマンスが約30〜40%改善
- **HTTP PATCH サポート**: `N/http` および `N/https` モジュールで PATCH メソッドが利用可能に（外部呼び出し・Suitelet 内部リクエスト両対応）

### 廃止予定（Deprecation）
- `N/currentRecord` モジュールの `getField()` メソッドが非推奨化 → 代替: `getFieldValue()`
- **2026.2（2026年9月予定）で完全削除**予定。早期の移行を推奨
- 出典: [BrokenRubik — NetSuite SuiteScript Update 2026](https://www.brokenrubik.com/blog/netsuite-2026-release-notes)

---

## SuiteCloud プラットフォーム更新

### SuiteCloud Developer Assistant（VS Code 拡張）
- VS Code の Cline プラグイン経由で利用できる AI コーディングアシスタント
- 自然言語プロンプトで SuiteScript 2.1 コードおよびユニットテストを自動生成
- SuiteCloud 拡張と Cline 拡張の両方のインストールが必要
- 出典: [NetSuite Brings AI-Powered Speed and Precision to SuiteCloud Development](https://www.prnewswire.com/news-releases/netsuite-brings-ai-powered-speed-and-precision-to-suitecloud-development-302754790.html)

### SuiteCloud Agent Skills（2026年4月 SuiteConnect SF 発表）
SuiteConnect San Francisco（2026年4月28日）で発表された AI コーディングエージェント向けの知識パッケージ群：
- **OWASP Security Reference Skill**: NetSuite 固有の OWASP セキュリティガイダンスをコーディング中にリアルタイム提供
- **SuiteScript Conversion Skill**: SuiteScript 1.0 → 2.1 の移行を自動化。APIマッピング、エントリポイント再構成、バリデーションレポート生成まで対応
- **User Interface Framework References Skill**: UI フレームワークに関するリファレンスをエージェントに提供
- 出典: [Knowledge Hub Media — SuiteConnect 2026 AI Coding Agent Skills](https://knowledgehubmedia.com/netsuite-suiteconnect-2026-new-ai-coding-agent-skills-for-suitecloud-developers/)

### Custom Tool Script Type（新規）
- 外部 AI クライアント（Claude、ChatGPT 等）が NetSuite の操作（レコード取得・作成など）を呼び出せる Custom Tool を開発者が定義できる新スクリプトタイプ
- **NetSuite AI Connector Service** を介して、LLM を NetSuite の直接インターフェースとして機能させることが可能
- 出典: [SuiteCloud Platform 2026.1 — netsuite.com](https://www.netsuite.com/portal/resource/articles/cloud-saas/suitecloud-platform-delivers-ai-native-development-expanded-rest-apis-and-next-generation-extensibility-in-netsuite-2026-1.shtml)

---

## REST API 更新

### REST API が SOAP と完全同等に（2026.1）
- 残存していた REST API のギャップを解消し、SuiteTalk SOAP との機能同等を達成
- **SOAP 新規エンドポイント追加の停止**: 2026.1 以降、各アップデートでの新規 SOAP エンドポイント追加は原則廃止。技術的・ビジネス的に不可欠な場合のみ追加

### 主な新機能
| 機能 | 概要 |
|---|---|
| **バッチ操作（Homogeneous Batch）** | 同一種別の複数操作を1回の REST コールで非同期送信。大量インポートや一括更新のスループット向上 |
| **Create-Form オペレーション** | 既存レコードからフォームフィールドを事前入力（例：受注から請求書作成）。UI ロジックを再現せず必要項目のみ追記して送信可能 |
| **動的フィールドオプション取得** | 特定レコード・フィールドの有効なドロップダウン選択肢を REST 経由で取得。外部 UI とのオプションリスト同期が容易に |
| **HTTP PATCH サポート** | 部分更新を行う標準的な REST パターンへの対応 |

- 出典: [SuiteCloud 2026: AI-Native, REST-First Innovation — CircularEdge](https://www.circularedge.com/blog/suitecloud-2026-platform-developer-updates/)

---

## AI 機能（業務向け）

### SuiteConnect 2026 発表の主要 AI 機能
- **Intelligent Close Manager**: 期末業務の集中ダッシュボード。AI による例外検知で異常を事前に把握
- **AI バンク・マッチング**: 生成 AI が銀行データをより構造的に解析し、自動照合率を大幅向上
- **EPM エージェント（計画・調整）**: 多段階の業務タスク（帳簿締め、銀行調整、顧客対応）を自律実行する Agentic ワークフロー
- **AI カスタマーサマリー**: ケースページ上に感情分析・メッセージ履歴・エスカレーション情報を自動要約して表示
- **AI 対応アドバンスドプライシング**: 日付範囲・商品群・顧客セグメントによるルールベース価格設定と AI 生成の価格サマリー
- 出典: [SuiteConnect 2026: Every AI Feature NetSuite Just Announced — BrokenRubik](https://www.brokenrubik.com/blog/suiteconnect-2026-netsuite-ai-announcements)

---

## まとめ

**NetSuite 2026.1** は AI と REST-First への戦略的転換を明確に示すリリースである。開発者にとって最大の変化は、① 新 `N/ai` モジュールによる AI 機能のスクリプト統合、② `async/await` サポート、③ REST API の SOAP 完全同等化（SOAP 新規追加の停止）の3点。
**SuiteCloud Agent Skills** の登場により、AI コーディングエージェントが NetSuite 固有の文脈を理解した上でスクリプト生成・移行を支援できるようになり、開発速度の大幅向上が期待できる。
**SuiteScript 1.0 → 2.1 移行** と **`getField()` → `getFieldValue()` 置換**（2026.2で削除）は今すぐ対応すべき技術的負債。SOAP 利用中のシステムは REST 移行計画の策定を急ぐべきである。

---

*レポート生成日: 2026-05-07 | 生成ツール: Claude Code Agent*
