# Codex用の差分

調整が必要なスキルだけ `<skill-name>/` 配下に差し替えるファイルを置く。
原本は `.claude/skills/`。設定方法と更新時の確認は親ディレクトリのREADMEを参照。

現在の差分：

- `cyk-gh-flow/`：スキル呼び出しにCodex用の共通規則を適用。Claude用のfrontmatter補助項目はCodex向け定義から外し、必要な前提・入力は本文に維持する。ブラウザとE2Eの選択は原本・Codex版とも共通ブラウザ入口に委ねる。
- `cyk-gh-flow-lite/`：ブラウザ操作は原本・Codex版とも共通入口に委ねる。Codex版ではClaudeの権限設定を検査せず、実際の承認手続きを使う。スキル起動をコミット許可とみなさず、明示的に許可された範囲だけ実行する。frontmatter補助項目は本文に移す。
