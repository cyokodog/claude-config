# Claude Code

## 自動モード（auto）で `gh pr merge` が止められる

- 自動判定が「レビューなしのマージ」として拒否する。拒否された後は、同じ目的の別コマンド（`gh pr list` など）も止められることがある。
- 個人 PJ でマージまで自動で回すなら、`~/.claude/settings.json` の `permissions.allow` に `Bash(gh pr merge:*)` を入れておく。
