---
name: cyk-note-claude-settings
description: グローバルなスキル・エージェント・ルールの詳細をそれぞれ個別のMarkdownファイルに記録する。/cyk-note-claude-settingsで実行。
disable-model-invocation: true
---

# Claude設定の記録スキル

このスキルは、グローバルに設定されているスキル・カスタムエージェント・ルールの内容を、それぞれ個別のMarkdownファイルとして記録します。

## 出力ファイルの種類

各定義ファイルに対して、以下の2種類のファイルを出力します。

### A. 説明ファイル（必ず生成）

定義ファイルの内部仕様をそのままコピーするのではなく、**利用者向けに整理した説明**を出力します。

- 使い方（起動方法・引数）
- 何をするか・動作モード
- アウトプット（生成・変更されるもの）
- 効果（使うことで何が嬉しいか）

### B. 日本語訳ファイル（元が英語の場合のみ生成）

定義ファイルの本文を**原文のまま日本語に翻訳**したファイルを出力します。

- 構成・見出し・手順・コードブロックは原文と同じ構造を維持する（文章のみ翻訳）
- 利用者向けに整理・要約しない。原文の忠実な日本語訳とする
- ファイル名は `{元のファイル名}__JP.md`

## 出力先

- **スキル A**: `$CLAUDE_SETTINGS_DIR/desc-skills/{スキル名}.md`
- **スキル B**: `$CLAUDE_SETTINGS_DIR/desc-skills/{スキル名}__JP.md`
- **エージェント A**: `$CLAUDE_SETTINGS_DIR/desc-agents/{エージェント名}.md`
- **エージェント B**: `$CLAUDE_SETTINGS_DIR/desc-agents/{エージェント名}__JP.md`
- **ルール A**: `$CLAUDE_SETTINGS_DIR/desc-rules/{ルール名}.md`
- **ルール B**: `$CLAUDE_SETTINGS_DIR/desc-rules/{ルール名}__JP.md`

## 実行手順

### 1. 更新対象の判定

各定義ファイルについて、以下の手順で処理対象かどうかを判定する。

```bash
# 定義ファイルのmtimeを取得
stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" ~/.claude/skills/{スキル名}/SKILL.md
```

出力ファイルが存在する場合、そのfrontmatterの `source_mtime` と比較する：
- 出力ファイルが存在しない → 処理対象
- `source_mtime` が現在のmtimeと異なる → 処理対象
- 一致する → スキップ（「スキップ: {名前}（更新なし）」と報告）

### 2. スキル一覧の処理

`~/.claude/skills/` 配下の各スキルディレクトリにある `SKILL.md` を読み込み、出力ファイルA・Bを生成する（「出力ファイルの種類」参照）。

**A（説明ファイル）** の形式（frontmatterを含む）：

```markdown
---
source: ~/.claude/skills/{スキル名}/SKILL.md
source_mtime: YYYY-MM-DD HH:MM:SS
---

# {スキル名}

最終更新: YYYY-MM-DD

## 概要

{descriptionの内容}

## 使い方

{起動方法・引数の説明}

## 何をするか

{動作の説明}

## アウトプット

{生成・変更されるものの説明}

## 効果

{使うことで得られるメリット}
```

**B（日本語訳ファイル）** は、元の SKILL.md が英語のみの場合に出力する。frontmatterの `source_mtime` はAと同じ値を記録する。

### 3. エージェント一覧の処理

`~/.claude/agents/` 配下の各 `.md` ファイルを読み込み、出力ファイルA・Bを生成する（「出力ファイルの種類」参照）。frontmatterの `source` は `~/.claude/agents/{エージェント名}.md` とする。

**B（日本語訳ファイル）** は、元のエージェント定義ファイルが英語のみの場合に出力する。frontmatterの `source_mtime` はAと同じ値を記録する。

### 4. ルール一覧の処理

`~/.claude/rules/` 配下の各 `.md` ファイルを読み込み、出力ファイルA・Bを生成する（「出力ファイルの種類」参照）。frontmatterの `source` は `~/.claude/rules/{ルール名}.md` とする。出力ファイル名はルール名から拡張子を除いたものとする。

**B（日本語訳ファイル）** は、元のルールファイルが英語のみの場合に出力する。frontmatterの `source_mtime` はAと同じ値を記録する。

### 5. 出力ディレクトリの確認

出力先ディレクトリが存在しない場合は `mkdir -p` で作成してから書き込む。

## 注意事項

- frontmatter（`source_mtime`）が一致するファイルはスキップされる
- 出力ファイルのfrontmatterはClaudeが更新判定に使うためのもので、本文には含めない
- 定義ファイルのfrontmatter（`---` で囲まれた部分）は本文には含めず、descriptionのみ概要欄に記載する
- 実行にはRead、Bash、Writeツールを使用する
