# 個人プロジェクトの進め方と、学びの残し方

対象: リポジトリのオーナーが `cyokodog` の個人プロジェクト（`gh repo view --json owner`）。仕事のプロジェクトには適用しない。

## 進め方

相談で方向が決まり、ユーザーが「issueにして」「進めて」などと言ったら `cyk-gh-flow-lite` スキルで回す。
承認は 2 回（Issue の作成時、マージの前）だけで、あとは止まらずに進める。

## 学びの仕分け

作業中に得た学び・経緯は、セッションで使い捨てずに次のどこかへ残す。どこに書くかは AI が判断し、マージ前の承認ゲートで案を示す。

| 内容 | 置き場所 |
|---|---|
| その Issue で起きた経緯・試行錯誤・判断（すったもんだ） | Issue 本文・コメント と `docs/issues/<N>/worklog.md` |
| そのプロジェクトで意味を持つ知見 | プロジェクトの `docs/knowledge/<topic>.md`（目次 `docs/knowledge/README.md`） |
| プロジェクトをまたいで役立つ知見 | `~/src/github.com/cyokodog/claude-config/knowledge/<topic>.md`（目次 `README.md`） |
| プロジェクトをまたいで守るルール | `~/src/github.com/cyokodog/claude-config/.claude/rules/<topic>.md`（`~/.claude/rules/` にリンク） |

- `docs/` 以下はディレクトリ名・ファイル名を英語、本文は日本語にする。
- 既存のファイルがあれば追記・更新する。同じ内容を複数の場所に重複して書かない（片方からもう片方へリンクする）。
- 横断ナレッジやルールを足したら、claude-config で commit する（このリポジトリは main に直接 commit して push する運用）。
