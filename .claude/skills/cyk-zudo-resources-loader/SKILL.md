---
name: cyk-zudo-resources-loader
description: >-
  ~/src/github.com/Takazudo/claude-resources のローカルリポジトリから指定されたスキル・エージェント・コマンド・フックをシンボリックリンクで取り込む。依存するリソースも芋づる式に自動取得する。ユーザーが「〇〇を取り込みたい」「〇〇をインストールして」などと言ったときに使用。取り込み完了後は cyk-note-claude-settings を自動実行する。
disable-model-invocation: true
---

# Zudo Resources Loader

`~/src/github.com/Takazudo/claude-resources` のローカルリポジトリから指定されたリソースを取得し、依存関係を芋づる式にシンボリックリンクで配置する。

## リポジトリ構造とローカル配置先

| ローカルリポジトリパス | 配置先 | 方法 |
|----------------------|--------|------|
| `skills/<name>/` | `~/.claude/skills/<name>` | ディレクトリへのシンボリックリンク |
| `agents/<name>.md` | `~/.claude/agents/<name>.md` | ファイルへのシンボリックリンク |
| `commands/<name>.md` | `~/.claude/commands/<name>.md` | ファイルへのシンボリックリンク |
| `hooks/<name>` | `~/.claude/hooks/<name>` | ファイルへのシンボリックリンク（実行権限付与） |

## 実行手順

### Step 1: ローカルリポジトリのリソース一覧を取得

```bash
REPO=~/src/github.com/Takazudo/claude-resources
ls "$REPO/skills"
ls "$REPO/agents"
ls "$REPO/commands"
ls "$REPO/hooks"
```

### Step 2: 取り込み対象を特定

ユーザーの指示から取り込むリソース名と種別（skill/agent/command/hook）を特定する。

### Step 3: 依存関係の芋づる取得

取り込み対象のファイルを読み込み、以下のパターンで依存を検出する。依存が見つかれば、それも同様に読み込み・依存検出を繰り返す（既に処理済みのものはスキップ）。

**依存検出パターン:**

1. **スキル参照**: `` `/skill-name` `` 形式（例: `` `/local-review` ``、`` `/watch-ci` ``）
2. **エージェント参照**: `subagent_type: "agent-name"` 形式
3. **スクリプト直接参照**: `~/.claude/skills/<name>/` や `~/.claude/agents/<name>` へのパス

検出した名前がローカルリポジトリの各ディレクトリに存在するか確認し、存在すれば取り込み対象に追加する。

### Step 4: シンボリックリンクで配置

**スキルの場合:**

```bash
REPO=~/src/github.com/Takazudo/claude-resources
ln -sf "$REPO/skills/<name>" ~/.claude/skills/<name>
```

**エージェントの場合:**

```bash
ln -sf "$REPO/agents/<name>.md" ~/.claude/agents/<name>.md
```

**コマンドの場合:**

```bash
ln -sf "$REPO/commands/<name>.md" ~/.claude/commands/<name>.md
```

**フックの場合:**

```bash
ln -sf "$REPO/hooks/<name>" ~/.claude/hooks/<name>
chmod +x "$REPO/hooks/<name>"
```

### Step 5: 出力ディレクトリの確認

配置先ディレクトリが存在しない場合は `mkdir -p` で作成してから書き込む。

### Step 6: 取り込み結果を表示

取り込んだリソースの一覧を以下の形式で表示する:

```
取り込んだリソース:
  skills:
    - local-review（新規）
    - watch-ci（新規）
    - pr-revise（依存・新規）
  agents:
    - code-reviewer（依存・新規）
  commands:
    （なし）
  hooks:
    （なし）
```

「新規」= 新規リンク作成、「更新」= 既存リンクを上書き（`ln -sf`）、「依存」= 芋づる式で取り込んだもの

### Step 7: cyk-note-claude-settings を実行

取り込み完了後、`/cyk-note-claude-settings` スキルを実行してドキュメントを更新する。

## 注意事項

- 既存リンクは `ln -sf` で上書きする
- スキルはディレクトリ単位でシンボリックリンクを張るため、サブディレクトリも自動的に参照される
- 依存検出は取り込んだファイルの内容に基づく（ローカルリポジトリに存在しないものはスキップ）
- `cyk-note-claude-settings` 自身や本スキル（`cyk-zudo-resources-loader`）は依存として取り込まない
