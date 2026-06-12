---
name: cyk-e2e-test-maker
description: >-
  Playwright形式のE2Eテストコードを生成するスキル。引数にファイル名・テスト内容・テスト対象URLを受け取り、
  Claude in Chromeで実際にページを操作してDOMを確認しながら、実際のDOM構造に基づく信頼性の高いセレクターを決定してテストコードを生成する。
  Use when: (1) ユーザーが「E2Eテストを生成して」「テストコードを作って」と言う, (2) ユーザーが `/cyk-e2e-test-maker` を実行する。
argument-hint: "<ファイル名> <テスト内容> [URL]"
---

# E2Eテストコード生成スキル

PlaywrightのE2Eテストコードを、実際のDOM構造を確認しながら生成する。

## 引数の確認

`$ARGUMENTS` から以下を読み取る。未指定の項目はコンテキストから読み取る。不可能な場合はユーザーに確認する。

- **ファイル名**: 生成するテストファイル名（例: `login.spec.ts`）
- **テスト内容**: テストで検証する操作・シナリオの説明
- **テスト対象URL**: アクセスするURL
- **保存先**: 生成するテストファイルを保存するディレクトリ

## 手順

### Step 1: ブラウザでURLにアクセス

Claude in Chromeのツールを使ってテスト対象のURLにアクセスする。

1. `mcp__claude-in-chrome__tabs_context_mcp` でタブの状態を確認
2. `mcp__claude-in-chrome__tabs_create_mcp` で新しいタブを作成
3. `mcp__claude-in-chrome__navigate` でテスト対象URLに移動

#### Claude in Chrome に接続できない場合

ユーザーに報告し、再接続を待つ。実装コードからセレクターを推測したり、ユーザー確認前にテストコードを書いてはいけない。

### Step 2: ページを操作しながらセレクターを確認

テスト内容に記述された操作をステップバイステップで行う。各ステップで以下を実施する。

1. `mcp__claude-in-chrome__read_page` または `mcp__claude-in-chrome__javascript_tool` でDOMを確認し、セレクター候補の要素を特定する
2. `mcp__claude-in-chrome__javascript_tool` で対象要素の以下を取得する：
   - テキスト: `textContent` をトリムした文字列
   - タグ: `tagName`（小文字）

```js
const el = document.querySelector("a.target-link");
({ text: el.textContent.trim(), tag: el.tagName.toLowerCase() });
// → { text: "ログイン", tag: "a" }
```

3. 取得したテキスト・タグを使い、以下のロケーター優先順位に従ってロケーターと一意性チェックをセットで実施する：

**テキスト指定のルール:** 文字列リテラルは禁止。正規表現を使い、以下を行うこと。

- 前後の空白・改行は常に `\s*` で除去する
- テキスト中に空白・改行が含まれる場合は `\s+` で除去する

```
❌ `getByRole("link", { name: "ログイン" })`
✅ `getByRole("link", { name: /^\s*ログイン\s*$/ })`
✅ `getByRole("heading", { name: /^\s*ご利用規約\s+同意して続ける\s*$/ })`
```

**1. getByRole（ARIAロール）**

```js
// ロケーター
getByRole("link", { name: /^\s*ログイン\s*$/ });
// 一意性チェック
const els = [...document.querySelectorAll("a")].filter((el) =>
  /^\s*ログイン\s*$/.test(el.textContent),
);
({ length: els.length });
```

**2. getByLabel（フォームコントロール）**

```js
// ロケーター
getByLabel(/^\s*メールアドレス\s*$/);
// 一意性チェック
const els = [...document.querySelectorAll("label")].filter((el) =>
  /^\s*メールアドレス\s*$/.test(el.textContent),
);
({ length: els.length });
```

**3. getByText（非インタラクティブ要素）**

```js
// ロケーター
getByText(/^\s*資料請求はこちら\s*$/);
// 一意性チェック（手順2で取得したタグを使う）
const els = [...document.querySelectorAll("p")].filter((el) =>
  /^\s*資料請求はこちら\s*$/.test(el.textContent),
);
({ length: els.length });
```

**4. getByTestId**

```js
// ロケーター
getByTestId("submit-btn");
// 一意性チェック
const els = document.querySelectorAll('[data-testid="submit-btn"]');
({ length: els.length });
```

**5. CSS / XPath（非推奨）**

```js
// ロケーター
locator(".btn-submit");
// 一意性チェック
const els = document.querySelectorAll(".btn-submit");
({ length: els.length });
```

単一のロケーターで一意にできない場合は、コンテナで絞ってから特定する。
コンテナの優先順位: ARIAロール → ページレイアウト上の領域を表すクラス名 → タグ名（非推奨）

※ `banner` ロールはページ最上位の `<header>` にのみ付与される。このサイトの構造上 `banner` は存在しないため使用禁止。

```js
locator(".cg-GlobalHeader").getByRole("link", { name: /^\s*ログイン\s*$/ });
```

それでも一意にできない場合はユーザーに相談する。

### Step 3: セレクター一覧のユーザー確認

セレクターが決定したら、以下の形式で一覧を提示し、ユーザーに確認を求める。

```
| # | ステップ | ロケーター | 一意性チェック件数 | 備考 |
|---|---------|-----------|-------------------|------|
| 1 | ログインリンクをクリック | getByRole('link', { name: 'ログイン' }) | 1 | |
| 2 | メールを入力 | getByLabel('メール') | 1 | |
```

**確認が必要な追加事項:**

- `一意性チェック件数` が `1` になっていること（複数件の場合はセレクターを見直す）
- 以下に該当するセレクターがある場合、**必ずその理由をユーザーに説明する**:
  - `getByRole`、`getByLabel`、`getByText` を採用できなかった
  - エリア（コンテナ）の絞り込み以外でクラスベースのセレクター（例: `locator('.btn-submit')`）を採用した

ユーザーからOKをもらってからテストコードを生成する。

### Step 4: テストコードの生成

確認済みのセレクターを使い、Playwrightのテストコードを生成し保存する。

テストコードのテンプレート:

```ts
import { test, expect } from "@playwright/test";

test("<テスト内容>", async ({ page }) => {
  await page.goto("<テスト対象URL>");

  await test.step("<ステップの説明>", async () => {
    // 各操作・アサーションを記述
  });
});
```

- 各ステップは `test.step()` で囲む
- `test.step()` の引数には、ユーザーから渡されたテスト内容をもとに、テストの意図が伝わる文言を使う

生成したコードをファイルに書き込んで完了。
