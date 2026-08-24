---
name: cyk-knowledge-post-from-claude-talk
description: 現在の会話履歴を読み取り、cyk-knowledgeブログに投稿する。/cyk-knowledge-post-from-claude-talk で実行。
---

# cyk-knowledge-post-from-claude-talk スキル

現在の Claude Code セッションの会話履歴を分析し、知見としてまとめて
~/src/github.com/cyokodog/cyk-knowledge に投稿する。

## 実行形式

```
/cyk-knowledge-post-from-claude-talk
```

## 実行手順

### 1. 会話履歴の分析

現在のセッションの会話履歴全体を読み取り、投稿候補となるトピックを抽出する。

トピックとして抽出する基準：

- 特定の問題を解決した経緯
- ツール・コマンド・設定の使い方を学んだ流れ
- 概念や仕組みについて理解を深めた議論
- ハマりどころと対処法

複数のトピックが見つかった場合は番号付きリストで提示し、どれを投稿するか選択を求める。以下は例。

```
以下のトピックが見つかりました：

1. Claude Code の deferred tools と ToolSearch の使い方
2. cyk-knowledge ブログの設計と構築
3. TypeScript で静的サイトジェネレーターを自作する方法

どれについて投稿しますか？（番号で答えてください）
```

トピックが1つだけの場合は選択を省略してそのまま進む。

### 2. タイトルとタグの提案

選択されたトピックについて：

**タイトル**: 会話内容から端的なタイトルを提案する。

**タグ**: `~/src/github.com/cyokodog/cyk-knowledge/posts/` 配下の全 `.md` ファイルの
フロントマターを読み取り、既存タグの一覧を把握する。
既存タグを優先して 1〜3 個提案し、適切なものがなければ新規タグを提案する。

以下の形式で提示してユーザーの確認を求める：

```
タイトル: Claude Code の deferred tools と ToolSearch の使い方
タグ: [claude-code, mcp]

このまま進めますか？タイトルやタグを変更する場合は教えてください。
```

### 3. 投稿内容の生成・調整

確認が取れたら、会話から得られた知見を以下の構成で Markdown に整形して提示する：

```markdown
---
title: { タイトル }
date: { 今日の日付 YYYY-MM-DD }
tags: [{ タグ1 }, { タグ2 }]
---

## 概要

{何についての知見か1〜2文で}

## {内容に応じた見出し}

{具体的な内容。コードブロック・箇条書きを適宜使う}
```

提示後、「このまま投稿しますか？修正点があれば教えてください。」と聞く。
ユーザーが修正を求めた場合は内容を更新して再提示する。これを合意が取れるまで繰り返す。

### 4. ファイル保存

合意が取れたら以下の手順で保存する。

**スラッグの生成**: タイトルを英単語に変換してハイフン区切りにする。
日本語タイトルの場合は内容から英語のスラッグを推測して生成する。

**ファイルパス**: `~/src/github.com/cyokodog/cyk-knowledge/posts/YYYY-MM-DD-{slug}.md`

`Write` ツールで保存する。

### 5. ビルド実行

```bash
cd ~/src/github.com/cyokodog/cyk-knowledge && npm run build
```

### 6. 完了報告

```
投稿しました。
ファイル: ~/src/github.com/cyokodog/cyk-knowledge/posts/2026-06-15-deferred-tools.md
確認: http://localhost:3000（serve が起動中の場合）
```

## 注意事項

- `~/` は `/Users/cyokodog/` に展開して使用する
- 日付は今日の日付を使用する
- スラッグは英小文字・ハイフン区切りにする
- 既存の posts/ ファイルを読むときはフロントマターのみ把握すれば十分（本文は不要）
