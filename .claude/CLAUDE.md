# Global Instructions

## ブラウザ操作

ブラウザを操作する作業では、先に `~/src/github.com/cyokodog/claude-config/.claude/shared/cyk-browser-operations.md` を読み、共通入口でツール・呼び先を選ぶ。各スキルにClaude／Codexごとの選択を複写しない。ユーザーの明示指定とスキル固有の承認・停止条件は維持する。

## スキル定義の変更後

`~/src/github.com/cyokodog/claude-config/` のスキル原本・Codex用の差分・同期設定を追加／変更／改名／削除したら、`tools/skill-sync/README.md` を読み、分類の更新と同期処理（check → apply → check）まで実行して作業完了とする。同期をユーザーに指示し直させない。原本は `.claude/skills/` に維持し、`.agents/skills/` は直接編集しない。同期失敗や未対応項目は報告する。別プロジェクトで変更した場合も同様。コミット・プッシュの権限は別途既存の指示に従う。

ユーザーが明示的に指示しない限り、`git commit` や `git push` を実行しない。
コミットとプッシュのタイミングはユーザーがコントロールする。
ファイルを編集した後は止まって待つ。「進捗を保存するため」などの理由でも、タスク完了時でも、自発的にコミットしない。

ただし PR を作成する場面では、対象ブランチの `git push` は確認を取らずに実行する。
PR を作るならブランチが push 済みである必要があるのは自明なので、いちいち聞かない。
push してよいのは PR 対象のブランチのみで、`commit` は上記のとおり従来どおり確認する。

ホームディレクトリ以下のパスは `/Users/cyokodog/` ではなく `~/` で表記する。

## 個人 PJ と仕事 PJ

- **仕事 PJ** は Issue ありきで、計画・実装を 1 つずつ確認しながら進める。進め方はその PJ 側にある AI 定義（CLAUDE.md や `.claude/`）に従う。
- **個人 PJ**（リポジトリのオーナーが `cyokodog`）は、相談で方向が決まったら `cyk-gh-flow-lite` で Issue 作成からマージまでスピード重視で回す。詳しくは `~/.claude/rules/personal-projects.md`。
