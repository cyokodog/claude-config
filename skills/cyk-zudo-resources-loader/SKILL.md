---
name: cyk-zudo-resources-loader
description: >-
  https://github.com/Takazudo/claude-resources から指定されたスキル・エージェント・コマンド・フックを取り込む。依存するリソースも芋づる式に自動取得する。ユーザーが「〇〇を取り込みたい」「〇〇をインストールして」などと言ったときに使用。取り込み完了後は cyk-note-claude-settings を自動実行する。
disable-model-invocation: true
---

# Zudo Resources Loader

`https://github.com/Takazudo/claude-resources` から指定されたリソースを取得し、依存関係を芋づる式にローカルへ配置する。

## リポジトリ構造とローカル配置先

| リポジトリパス | ローカル配置先 | 備考 |
|---------------|---------------|------|
| `skills/<name>/` | `~/.claude/skills/<name>/` | ディレクトリごと |
| `agents/<name>.md` | `~/.claude/agents/<name>.md` | 単一ファイル |
| `commands/<name>.md` | `~/.claude/commands/<name>.md` | 単一ファイル |
| `hooks/<name>` | `~/.claude/hooks/<name>` | 実行権限付与 |

## 実行手順

### Step 1: リポジトリのリソース一覧を取得

```bash
gh api "repos/Takazudo/claude-resources/contents/skills" --jq '.[].name'
gh api "repos/Takazudo/claude-resources/contents/agents" --jq '.[].name'
gh api "repos/Takazudo/claude-resources/contents/commands" --jq '.[].name'
gh api "repos/Takazudo/claude-resources/contents/hooks" --jq '.[].name'
```

### Step 2: 取り込み対象を特定

ユーザーの指示から取り込むリソース名と種別（skill/agent/command/hook）を特定する。

### Step 3: 依存関係の芋づる取得

取り込み対象のファイルを取得し、以下のパターンで依存を検出する。依存が見つかれば、それも同様に取得・依存検出を繰り返す（既に処理済みのものはスキップ）。

**依存検出パターン:**

1. **スキル参照**: `` `/skill-name` `` 形式（例: `` `/local-review` ``、`` `/watch-ci` ``）
2. **エージェント参照**: `subagent_type: "agent-name"` 形式
3. **スクリプト直接参照**: `~/.claude/skills/<name>/` や `~/.claude/agents/<name>` へのパス

検出した名前がリポジトリの各ディレクトリに存在するか確認し、存在すれば取り込み対象に追加する。

### Step 4: リソースを取得してローカルに配置

**スキルの場合:**

```bash
# ディレクトリ内のファイル一覧を取得
gh api "repos/Takazudo/claude-resources/contents/skills/<name>" --jq '.[].name'

# 各ファイルを取得（サブディレクトリも再帰的に処理）
gh api "repos/Takazudo/claude-resources/contents/skills/<name>/<file>" --jq '.content' | base64 -d > ~/.claude/skills/<name>/<file>

# スクリプトファイルには実行権限を付与
chmod +x ~/.claude/skills/<name>/scripts/*.sh 2>/dev/null || true
```

**エージェントの場合:**

```bash
gh api "repos/Takazudo/claude-resources/contents/agents/<name>.md" --jq '.content' | base64 -d > ~/.claude/agents/<name>.md
```

**コマンドの場合:**

```bash
gh api "repos/Takazudo/claude-resources/contents/commands/<name>.md" --jq '.content' | base64 -d > ~/.claude/commands/<name>.md
```

**フックの場合:**

```bash
gh api "repos/Takazudo/claude-resources/contents/hooks/<name>" --jq '.content' | base64 -d > ~/.claude/hooks/<name>
chmod +x ~/.claude/hooks/<name>
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

「新規」= 新規追加、「更新」= 既存を上書き、「依存」= 芋づる式で取り込んだもの

### Step 7: cyk-note-claude-settings を実行

取り込み完了後、`/cyk-note-claude-settings` スキルを実行してドキュメントを更新する。

## 注意事項

- 既存ファイルは上書きする（バージョン管理はリポジトリ側で行う）
- スキルのサブディレクトリ（`scripts/` 等）も再帰的に取得する
- 依存検出は取り込んだファイルの内容に基づく（リポジトリに存在しないものはスキップ）
- `cyk-note-claude-settings` 自身や本スキル（`cyk-zudo-resources-loader`）は依存として取り込まない
