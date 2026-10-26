# claude-config

Claude Codeの共通設定と横断ナレッジを管理するリポジトリ。
Claude Code側を原本として維持し、Codex向けのスキルは同期ツールで構成する。

- `.claude/`：Claude Codeの設定・スキル・共通資料の原本
- `.agents/skills/`：このプロジェクトのCodex用スキル出力（直接編集しない）
- `tools/skill-sync/`：スキルの分類・同期・検証。詳細は [操作説明](tools/skill-sync/README.md)
- `tools/playwright-mcp/`：Node切り替えの影響を受けない、両製品共通の [Playwright MCP実行環境](tools/playwright-mcp/README.md)
- `tools/browser/`：ブラウザ操作・E2Eのツールとスキルを選ぶ共通処理。[入口の手順](.claude/shared/cyk-browser-operations.md) に従いAIが呼び出す
- `AGENTS.md`：Codexから既存の共通指示を読むための入口
- `knowledge/`：プロジェクトをまたぐ知見

定義を変更したAIが同期・検証まで行う。常駐監視は使わない。
初版ではユーザー共通のCodexスキル配置やエージェント変換は扱わない。
