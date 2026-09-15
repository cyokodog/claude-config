---
name: cyk-doc-fetch
description: 技術系英語ドキュメントサイトのページ一式を逐語のまま取得し、en/（英語原文）ディレクトリに保存するスキル。取得したドキュメントは cyk-doc-ask で参照して会話に使う。「ドキュメントを取得して」「ドキュメントをローカルに保存して」「ドキュメントを落としてきて」のように言われたらこのスキルを使う。引数にURLを指定する。
argument-hint: <docs-url> [--dir <path>]
disable-model-invocation: false
---

# cyk-doc-fetch

技術系英語ドキュメントサイトを**逐語のまま**取得し、`en/`（英語原文）に保存するスキル。

保存したドキュメントは `cyk-doc-ask` で参照し、根拠を持った会話に使う。
日本語訳が必要な場合は `cyk-doc-translate` を使う（このスキルは翻訳しない）。

## 鉄則：WebFetch でページ本文やナビを取得しない

**WebFetch は「ページそのもの」ではなく、小型モデルが要約した応答を返す。**

実際に、Playwright のサイドバーを WebFetch で解析したところ
Migration が 3件→1件、Integrations が 3件→1件に削られていた（sitemap との照合で検出）。

- **本文の欠落** → 根拠として使えないドキュメントになる
- **ナビの欠落** → そもそもページ一覧が欠け、取得漏れに気付けない

したがって**ナビ抽出（Step 2）・本文取得（Step 4）の両方**を逐語ソースから行う。
WebFetch を使ってよいのは「リポジトリの所在を調べる」程度の探索用途に限る。

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

### Step 2: 逐語ソースの特定

**このステップの目的は「ページ本文の取得元」と「正しいページ一覧」を同時に確定すること。**

#### 2-1. ドキュメントのソースリポジトリを探す

多くのドキュメントサイトは markdown 原稿を公開リポジトリで管理している。以下の順で探す。

1. ページ内の **「Edit this page」「Edit on GitHub」リンク** — 原稿ファイルの位置を直接指す最短経路
2. **フッター・ヘッダーのリポジトリリンク**
3. サイト名から推測（`playwright.dev` → `microsoft/playwright`）

```bash
# Edit this page リンクを探す（要約を挟まないよう curl で生HTMLを見る）
curl -sL "<url>" | grep -oE 'https://github\.com/[^"]*(edit|blob)/[^"]*'
```

原稿ディレクトリの典型例：`docs/src/`、`docs/`、`content/`、`src/content/docs/`

#### 2-2. 逐語であることを検証する（必須）

**1ファイルだけ取得し、逐語の markdown かどうかを目視確認する。**

```bash
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<docs-dir>/<file>.md" | head -40
```

確認する点：

- markdown の生テキストか（HTML やエラーページでないか）
- 見出し・コードブロックが原形のままか
- frontmatter があるか（`---` で始まるか）

**逐語でなければ次の候補に移る。** ここで妥協すると全ページが汚染される。

#### 2-3. ページ一覧を確定する

**サイドバーの HTML を解析してはいけない**（要約による欠落が起きる）。代わりにリポジトリ内の**ナビ定義ファイル**を読む。

| サイトジェネレータ | ナビ定義ファイル |
| ------------------ | ---------------- |
| Docusaurus | `sidebars.js` / `sidebars.ts` |
| MkDocs | `mkdocs.yml` の `nav:` |
| VitePress | `.vitepress/config.*` の `sidebar` |
| mdBook / GitBook | `SUMMARY.md` |
| Sphinx | `_toc.yml` / `index.rst` の `toctree` |
| Astro Starlight | `astro.config.*` の `sidebar` |

```bash
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path-to-nav-file>"
```

#### 2-4. sitemap.xml と突き合わせる（必須）

**この照合が、実際にナビ欠落を検出した唯一の手段。省略しない。**

```bash
curl -sL "<site-root>/sitemap.xml" | grep -oE '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g'
```

ナビ定義から得た一覧と付き合わせ、**差分を必ずユーザーに提示する**。

- **ナビにあり sitemap にない** → 非公開・リダイレクトの可能性。要確認
- **sitemap にありナビにない** → 別ツリー（API リファレンス等）の可能性。取得対象に含めるかをユーザーに確認する

#### 2-5. フォールバック：公開リポジトリがない場合

原稿リポジトリが見つからないサイトもある。その場合は **HTML を取得してローカルで markdown 化する**。
モデルを介さない変換であれば要約による欠落は起きない。

```bash
# 生HTMLを保存し、変換ツールにかける（pandoc 等）
curl -sL "<url>" -o page.html
pandoc -f html -t gfm page.html -o page.md
```

ページ一覧は `sitemap.xml` を主たる情報源にする。
**この経路を使った場合は、その旨を完了報告に明記する**（逐語性の水準が異なるため）。

#### 2-6. 命名

**サイト名：** ドメインから導出する（例: `playwright.dev` → `playwright`、`docs.example.com` → `example`）。

**ファイル名：** ナビ定義の順序と見出しラベルから生成する。

- カテゴリ: `NN-category-name/`（例: `01-introduction/`、`02-guides/`）
- ページ: `NN-page-name.md`（例: `01-getting-started.md`、`02-routing.md`）
- 連番はナビ定義上の並び順から割り当てる

### Step 3: 構造確認

探索結果をユーザーに提示し、確認を得てから取得を開始する。

```
## 取得予定の構造

サイト名: <name>
出力先: <ベースディレクトリ>/<name>/
取得元: https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<docs-dir>/
        （逐語 markdown であることを検証済み）
ナビ定義: <nav file>

### sitemap との差分
- sitemap のみに存在: <別ツリーのパス>（N ページ） → 含めますか？
- ナビのみに存在: なし

### カテゴリ一覧
- 01-introduction/ (4ページ)
- 02-guides/ (15ページ)
- ...

### ページ一覧
01-introduction/
  01-getting-started.md  →  <url>
  02-why-playwright.md   →  <url>
  ...
```

**sitemap との差分は必ず提示する。** 黙って落とすと、欠けたことにユーザーが気付けない。

既存ディレクトリがある場合は上書き確認をする。

### Step 4: en/ ディレクトリを作成

Step 2 で確定した**逐語ソース**から各ページを取得し、`<name>/en/` 配下に保存する。

```bash
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<docs-dir>/<file>.md"
```

**取得内容は改変しない。** 要約・整形・省略をせず、本文をそのまま保存する。
原稿に frontmatter がある場合は取り除いてよい（タイトルはヘッダーに反映する）。

**ファイルヘッダー形式（必須）：**

```markdown
# <Page Title> | <Site Name>

Source: <サイト上のページURL>
Raw: <取得に使った raw URL>

<本文（逐語）>
```

`Source:` は**サイト上の人間が読めるURL**にする（`cyk-doc-ask` がユーザーに出典として示すため）。
`Raw:` は再取得用の記録。

**index.md の作成：** `<name>/en/index.md` に英語でTOCを作成する。

この index.md は `cyk-doc-ask` が「どのファイルを読むべきか」を判断する唯一の索引になる。
**Description と Keywords の質が回答精度を直接左右する**ため、手を抜かずに書くこと。

形式：

```markdown
# <Site Name> Documentation

Official site: <root url>
Source repository: <repo url>

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

### Step 5: 完了報告

```
## 完了

出力先: <ベースディレクトリ>/<name>/
└── en/   （英語原文: XX ページ）

取得元: <raw base url>（逐語 markdown）
sitemap 照合: 差分なし / <差分の内容>

参照するには:
  /cyk-doc-ask <質問>

日本語訳が必要なら:
  /cyk-doc-translate <name> <ページ指定>
```

HTML→markdown 変換のフォールバック経路を使った場合は、その旨を明記する。

保存先が既定の `refs/` 配下の場合、`cyk-knowledge` リポジトリは git 管理下にある。
**コミットはユーザーが行うため、スキル側では commit / push しない。**

## 注意

- **このスキルは翻訳しない。** `ja/` を作るのは `cyk-doc-translate` の役割
- `cyk-doc-ask` は `en/` のみを根拠に読むため、`en/` の逐語性がこの仕組み全体の土台になる
