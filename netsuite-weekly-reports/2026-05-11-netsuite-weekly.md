# NetSuite 週次テックレポート — 2026-05-11

## 更新情報・リリースノート

### NetSuite 2026.1 リリース概要
- 2026年2月中旬〜4月末にかけてプロダクション環境へのアップグレードが展開
- AI・財務・サプライチェーン・開発者ツール全域にわたる大規模アップデート
- 次回 2026.2 リリースは2026年9月を予定
- 出典: [Oracle NetSuite 2026.1 Release Notes](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_N3944673.html)

### 重要：SOAPエンドポイントの段階的廃止
- **2026.1 より**、新規リリースでの SOAP Web Services エンドポイント提供を終了
- **2027.1 より**、TBA（Token-Based Authentication / OAuth 1.0）を使った新規インテグレーション作成が不可になる（既存インテグレーションは継続動作）
- **2027.1 より**、OAuth 2.0 認可コードフローで PKCE（Proof Key for Code Exchange）が必須化
- SuiteCloud SDK 24.1 が TBA / OAuth 1.0 をサポートする最終バージョン
- 出典: [NetSuite TBA to OAuth 2.0 Migration Guide](https://www.houseblend.io/articles/netsuite-tba-oauth2-migration-2027) / [BrokenRubik Developer Notes](https://www.brokenrubik.com/blog/netsuite-2026-1-release-notes-developers-it-architects)

---

## 技術記事

### SuiteScript 2.1 — Async/Await 対応 & N/ai モジュール追加
- Map/Reduce・Scheduled スクリプトで `async/await` が正式サポート。コールバックチェーンを排除し、`try/catch` によるエラーハンドリングが可能に
- 新モジュール **N/ai** が追加。サーバーサイドスクリプトから直接 AI 機能を呼び出せる
  - `ai.classify()` / `ai.extract()` / `ai.summarize()` / `ai.generate()`
- **破壊的変更予告**：`N/currentRecord` の `getField()` が非推奨 → `getFieldValue()` へ移行必須。2026.2 で削除予定
- 出典: [SuiteCloud Platform 2026.1 — NetSuite](https://www.netsuite.com/portal/resource/articles/cloud-saas/suitecloud-platform-delivers-ai-native-development-expanded-rest-apis-and-next-generation-extensibility-in-netsuite-2026-1.shtml)

### N/query モジュール — CTE サポート & パフォーマンス向上
- **Common Table Expressions (CTE)** をサポート。複雑な分析クエリの可読性が大幅に向上
- サブクエリのパフォーマンスが推定 30〜40% 改善
- 出典: [NetSuite 2026.1 Deep Dive — Moss Adams](https://www.mossadams.com/articles/2026/04/netsuite-release-march-2026)

### SuiteCloud Developer Assistant（AI コーディングアシスタント）
- VS Code + **Cline プラグイン** 統合により、自然言語プロンプトから SuiteScript 2.1 コード（ユニットテスト含む）を自動生成
- **SuiteCloud Agent Skills** として以下の知識パッケージを提供：
  - UI Framework References Skill
  - OWASP Security Reference Skill（NetSuite 固有のセキュリティガイダンス）
  - SuiteScript Conversion Skill（v1.0 → v2.1 移行支援）
- 出典: [SuiteConnect 2026 AI Coding Agent Skills — Knowledge Hub Media](https://knowledgehubmedia.com/netsuite-suiteconnect-2026-new-ai-coding-agent-skills-for-suitecloud-developers/)

### REST API 強化 — バッチ操作 & MCP 対応 AI コネクタ
- **バッチ操作**：1 回の REST 呼び出しで複数の同種オペレーションを非同期実行可能。大量インポートや一括更新のスループットが向上
- **NetSuite AI Connector Service**：Model Context Protocol（MCP）に対応した新しい統合サービス。Claude・ChatGPT などの生成 AI アプリから NetSuite のデータ取得・トランザクション操作・レコード作成を直接実行可能
- **カスタムツールスクリプト**：外部 AI クライアントが NetSuite AI Connector 経由で呼び出せるカスタムツールを開発者が実装できる新スクリプトタイプ
- 出典: [NetSuite REST API Developer Guide 2026 — BrokenRubik](https://www.brokenrubik.com/blog/netsuite-rest-api-guide)

### AI 財務機能（2026.1）
- **Intelligent Close Manager**：期末処理の一元管理ビューと AI による異常検知。問題を早期にサーフェス化
- **銀行取引マッチング**：生成 AI が銀行データを構造化し、自動マッチング率を向上。手動介入を大幅削減
- **CRM AI アシスタント**：ケースページ上にケースのサマリー（感情分析・メッセージ履歴・エスカレーション）を自動生成
- **Advanced Pricing**：コストプラス価格設定エンジンと AI 生成の価格サマリー（在庫水準・コスト・販売履歴を統合）
- 出典: [NetSuite 2026.1 Features — NetSuite.com](https://www.netsuite.com/portal/resource/articles/financial-management/netsuite-2026-1-features-new-ai-close-and-cash-management-ai-agents-for-planning-and-reconciliation-and-more.shtml)

---

## まとめ

NetSuite 2026.1 は **AI ネイティブ化** と **REST/OAuth 2.0 への完全移行** が最大のテーマ。開発者は `N/currentRecord.getField()` の非推奨と **2027.1 での TBA 廃止** に今すぐ対応計画を立てる必要がある。SuiteScript では `async/await` と新 `N/ai` モジュールにより、よりモダンな非同期コードと AI 連携が可能になった。REST バッチ操作と MCP 対応 AI コネクタは、外部 AI システムと NetSuite を繋ぐ新たなアーキテクチャを切り拓く。管理者・開発者ともに、認証方式（TBA → OAuth 2.0）と API 方式（SOAP → REST）の二重移行を見据えたロードマップの策定が急務となっている。
