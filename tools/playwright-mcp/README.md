# 共通のPlaywright MCP実行環境

Claude CodeとCodexから同じローカルインストールを起動する。プロジェクトのNode切り替えには追従しない。

- 本体：このディレクトリの `node_modules/@playwright/mcp/`
- バージョン：`package.json` と `package-lock.json` に固定
- Node：`~/.nodenv/versions/22.19.0/bin/node` に固定（既存のインストールを使用）
- 起動：`/bin/bash` にこのディレクトリの `start.sh` の絶対パスを渡す

起動時はダウンロード・npm・npx・nodenvのshimを使わない。子プロセスのPATHも固定Nodeを先頭にする。作業ディレクトリや `NODENV_VERSION`、`.node-version` による切り替えの影響を受けない。固定したNodeを削除した場合はエラーを出し、別のNodeへの自動フォールバックはしない。

## 初回導入・別マシンでの復元

Nodeを上のパスに用意してから、リポジトリのルートで実行する。

```bash
~/.nodenv/versions/22.19.0/bin/node \
  ~/.nodenv/versions/22.19.0/lib/node_modules/npm/bin/npm-cli.js \
  ci --prefix tools/playwright-mcp --ignore-scripts --no-audit --no-fund

python3 tools/playwright-mcp/configure.py check
python3 tools/playwright-mcp/configure.py apply
python3 tools/playwright-mcp/configure.py check
```

設定反映先は `~/.claude.json` と `~/.codex/config.toml`。Claudeの既存プロジェクト内の `playwright` 定義も同じランチャーにそろえる。ユーザー設定を上書きするため、確認してから `apply` する。元の設定全体のバックアップは `.skill-sync/mcp-config-backups/` に作り、Git管理から除外・ファイルのアクセス権を制限する。バックアップには元の設定の秘密情報が含まれる可能性があるため共有しない。

既存のブラウザ引数・無関係の設定は維持する。見慣れない起動方式や複雑なTOML記述は自動変換せず停止する。Claudeの設定はJSONとして保存し直すので整形の差分が出ることがある。複数設定の更新は単一トランザクションではない。途中失敗時はバックアップと設定を確認する。

## ブラウザとログイン状態

既存のCodex設定は、インストール済みChromeと `~/.codex/playwright-profile` を引き続き使う。新設のClaude共通設定は、同じChrome実行ファイルと `~/.claude/playwright-profile` を使う。既存のClaudeプロジェクト設定にブラウザ引数があればそのまま維持する。

MCP本体は共有するが、同時起動時のブラウザプロファイル競合を避けるため、ClaudeとCodexの新設共通設定はプロファイルを分ける。通常のChromeのログイン状態を自動で引き継ぐ構成ではない。普段のログイン済みタブに接続する必要があるスキルでは、拡張接続などを別途検討する。同じ製品で複数のチャットが同一プロファイルを同時利用すると競合する場合もある。

設定変更後はMCPの再接続、または各アプリ／セッションの再起動が必要。動作中のMCPプロセスはそのまま入れ替わらない。別プロジェクトに同名のMCP定義があると、その設定が優先される場合がある。クラウドなど別マシンの環境にはこのローカル配置は適用されない。

## 更新

日常のNode切り替え時には何もしない。MCPを更新したいときだけ、固定Nodeのnpmで特定バージョンを `install --save-exact` し、ロックファイルと動作を確認する。固定Nodeの更新は `start.sh` とこの説明の両方を更新して検証する。ブラウザ操作のスキルやGHフローの呼び先の調整は、この実行環境の設定とは別の変更として扱う。

## 検証

```bash
/bin/bash tools/playwright-mcp/start.sh --version
python3 -m unittest discover -s tools/playwright-mcp -p 'test_*.py' -v
```
