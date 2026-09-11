---
name: cyk-doc-fetch
description: 技術系英語ドキュメントサイトのページ一式をローカルに保存し、en/（英語原文）とja/（日本語翻訳）ディレクトリに整理するスキル。取得したドキュメントは cyk-doc-ask で参照して会話に使う。「ドキュメントを取得して」「ドキュメントをローカルに保存して」「ドキュメントを翻訳して保存して」「fetch-doc-translator」のように言われたらこのスキルを使う。引数にURLを指定する。
argument-hint: <docs-url> [--dir <path>]
disable-model-invocation: false
---

# cyk-doc-fetch

技術系英語ドキュメントサイトを取得し、`en/`（英語原文）と `ja/`（日本語翻訳）ディレクトリで保存するスキル。

保存したドキュメントは `cyk-doc-ask` スキルで参照し、根拠を持った会話に使う。

## 手順

### Step 1: パラメータ解決

`$ARGUMENTS` から以下を抽出する。

- **URL**: 必須。未指定なら会話履歴から推測し、それでも不明ならユーザーに確認する。
- **`--dir <path>`**: 任意。保存先のベースディレクトリ。

**保存先の決定：**

1. `--dir <path>` の指定があればそれをベースにする
2. なければ既定値 `~/src/github.com/cyokodog/cyk-knowledge/refs/` を使う

最終的な出力先は `<ベースディレクトリ>/<name>/` となる（`<name>` は Step 2 で決定）。

既定の `refs/` は個人ナレッジの集約先。`cyk-doc-ask` が既定でここを探索するため、特段の理由がなければ既定のままにする。プロジェクトに含めたい場合のみ `--dir ./docs` のように指定する。

### Step 2: サイト構造の探索

指定URLのページを WebFetch で取得し、ナビゲーション構造を解析する。

探索の優先順位：

1. 指定URLのページのナビゲーション HTML からリンク一覧を抽出
2. `/sitemap.xml` の存在を確認（あれば補完に使う）
3. ドキュメントルート（`/docs/` など）を推定してナビを再取得

**サイト名の決定：** ドメインから導出する（例: `flueframework.com` → `flue`、`docs.example.com` → `example`）。

**ファイル名の命名規則：** サイトのナビゲーション順序と見出しラベルから生成する。

- カテゴリ（セクション）: `NN-category-name/`（例: `01-introduction/`、`02-guides/`）
- ページ: `NN-page-name.md`（例: `01-getting-started.md`、`02-routing.md`）
- 連番はナビ上の並び順から割り当てる

### Step 3: 構造確認

探索結果をユーザーに提示し、確認を得てから取得を開始する。

```
## 取得予定の構造

サイト名: <name>
出力先: <ベースディレクトリ>/<name>/

### カテゴリ一覧
- 01-introduction/ (4ページ)
- 02-guides/ (15ページ)
- ...

### ページ一覧
01-introduction/
  01-getting-started.md  →  <url>
  02-why-flue.md         →  <url>
  ...
```

既存ディレクトリがある場合は上書き確認をする。

### Step 4: en/ ディレクトリを作成

各ページを WebFetch で取得し、`<name>/en/` 配下に保存する。

**ファイルヘッダー形式（必須）：**

```markdown
# <Page Title> | <Site Name>

Source: <url>

<本文>
```

**index.md の作成：** `<name>/en/index.md` に英語でTOCを作成する。

この index.md は `cyk-doc-ask` が「どのファイルを読むべきか」を判断する唯一の索引になる。
**Description と Keywords の質が回答精度を直接左右する**ため、手を抜かずに書くこと。

形式：

```markdown
# <Site Name> Documentation

Official site: <root url>

<1-2行の概要説明>

---

## <Category Name>

| Page | File | Description | Keywords |
| ---- | ---- | ----------- | -------- |
| [Title](./path/to/file.md) | `path/to/file.md` | 1-2文でそのページが何を扱うかを具体的に書く | `apiName`, `configKey`, `term` |
```

**Description の書き方：**

- 1〜2文。「このページを読むと何が分かるか」を具体的に書く
- 悪い例: `Configuration guide`
- 良い例: `Explains how to configure the dev server, including port, host, and HTTPS options. Covers both CLI flags and config file fields.`

**Keywords の書き方：**

- そのページに登場する**主要なAPI名・設定キー・クラス名・専門用語**をカンマ区切りで列挙する（5〜15個程度）
- 原文の表記をそのまま使う（`defineConfig`, `server.port` のように）
- 検索で引っかかる語を優先し、一般語（`guide`, `usage`）は入れない

カテゴリ・ページのリンクはすべて英語のまま。

### Step 5: ja/ ディレクトリを作成

`en/` のファイルをすべて `ja/` にコピーし、各ファイルを日本語に翻訳する。

**翻訳ルール：**

- 本文・見出し・説明文を日本語化する
- コードブロック内のコードは翻訳しない（コメントは日本語化してよい）
- **API名・設定キー・クラス名などの識別子は翻訳しない**（原文表記を維持する）
- ファイルヘッダーは以下の形式に変える：

```markdown
# <日本語タイトル> | <Site Name>

原文: <url>

<本文（日本語）>
```

**index.md の翻訳：** `<name>/ja/index.md` はページタイトルを日本語化し、Description も日本語にする。
**Keywords 列は英語のまま維持する**（識別子は翻訳すると検索できなくなるため）。

形式：

```markdown
# <Site Name> ドキュメント（日本語版）

公式サイト: <root url>

<1-2行の概要説明（日本語）>

---

## <カテゴリ名（日本語）>

| ページ | ファイル | 概要 | キーワード |
| ------ | -------- | ---- | ---------- |
| [日本語タイトル](./path/to/file.md) | `path/to/file.md` | 概要説明（日本語、1-2文） | `apiName`, `configKey` |
```

### Step 6: 完了報告

```
## 完了

出力先: <ベースディレクトリ>/<name>/
├── en/   （英語原文: XX ページ）
└── ja/   （日本語翻訳: XX ページ）

参照するには:
  /cyk-doc-ask <質問>
```

保存先が既定の `refs/` 配下の場合、`cyk-knowledge` リポジトリは git 管理下にある。
**コミットはユーザーが行うため、スキル側では commit / push しない。**
