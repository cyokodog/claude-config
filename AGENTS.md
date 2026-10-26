# Codexでこのリポジトリを扱うとき

Claude Code側の定義を原本とする。作業前に次を読む。

- `.claude/CLAUDE.md`：全プロジェクト共通の行動指示。スキル変更後の同期手順も含む。
- `CLAUDE.md`：このリポジトリの構成とClaude Code側のリンク維持手順。
- `.claude/rules/knowledge-index.md`：横断ナレッジの入口。
- 個人プロジェクトの開発では `.claude/rules/personal-projects.md`、UI変更では `.claude/rules/cyk-design-system.md` も読む。

`.claude/rules/` をCodexがClaude Codeと同様に自動適用すると仮定しない。対象条件を確認して必要なファイルを読む。指示が競合するときはユーザーの明示的な指示を優先し、コミットは明示的な依頼がある場合のみ行う。

共有スキルから別のスキルを呼ぶ場合は `tools/skill-sync/codex-compatibility.md` を読み、Claudeの `Skill` ツールを使う記述をCodexでのスキル読込・実行に読み替える。承認・停止条件は維持する。

ブラウザ操作のツール・E2Eスキルの選択は `.claude/shared/cyk-browser-operations.md` の共通入口を使う。個別スキルに環境別の分岐を複写しない。

## スキル同期

原本は `.claude/skills/`。Codex用出力は `.agents/skills/`。
スキル原本・差分・同期設定を変更したら `tools/skill-sync/README.md` を読み、分類の更新と check → apply → check まで行う。出力先は直接編集しない。未分類や衝突を無視して完了扱いにしない。

Codex専用の権限・モデル・MCP・エージェント設定は共通化の対象外。Claude Codeの設定項目や専用ツールがCodexでも同じように働くと仮定しない。
