# claude-config

Claude Codeの共通設定と横断ナレッジを管理するリポジトリ。
Claude Code側を原本として維持し、Codex向けのスキルは同期ツールで構成する。

- `.claude/`：Claude Codeの設定・スキル・共通資料の原本
- `.agents/skills/`：このプロジェクトのCodex用スキル出力（直接編集しない）
- `.codex/`：Git管理するCodex用プロジェクト設定。エージェントは `.claude/agents/` の原本を読む最小限の定義
- `tools/skill-sync/`：スキルの分類・同期・検証。詳細は [操作説明](tools/skill-sync/README.md)
- `tools/playwright-mcp/`：Node切り替えの影響を受けない、両製品共通の [Playwright MCP実行環境](tools/playwright-mcp/README.md)
- `tools/browser/`：ブラウザ操作・E2Eのツールとスキルを選ぶ共通処理。[入口の手順](.claude/shared/cyk-browser-operations.md) に従いAIが呼び出す
- `AGENTS.md`：Codexから既存の共通指示を読むための入口
- `knowledge/`：プロジェクトをまたぐ知見

定義を変更したAIが同期・検証まで行う。常駐監視は使わない。
初版ではユーザー共通のCodexスキル配置やエージェント変換は扱わない。

`.agents/` と `.playwright-mcp/` はGit管理から除外する。スキル出力は `python3 tools/skill-sync/sync.py apply` で再生成し、ブラウザの操作ログ・画像は作業データとして扱う。
