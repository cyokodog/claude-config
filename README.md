# claude-config

Claude Codeの共通設定と横断ナレッジを管理するリポジトリ。
Claude Code側を原本として維持し、Codex向けのスキルは同期ツールで構成する。

- `.claude/`：Claude Codeの設定・スキル・共通資料の原本
- `.agents/skills/`：このプロジェクトのCodex用スキル出力（直接編集しない）
- `tools/skill-sync/`：スキルの分類・同期・検証。詳細は [操作説明](tools/skill-sync/README.md)
- `AGENTS.md`：Codexから既存の共通指示を読むための入口
- `knowledge/`：プロジェクトをまたぐ知見

定義を変更したAIが同期・検証まで行う。常駐監視は使わない。
初版ではユーザー共通のCodexスキル配置やエージェント変換は扱わない。
