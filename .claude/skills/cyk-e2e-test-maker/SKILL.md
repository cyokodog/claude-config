---
name: cyk-e2e-test-maker
description: >-
  Playwright形式のE2Eテストコードを生成するスキル。引数にファイル名・テスト内容・テスト対象URLを受け取り、
  Playwright MCPで実際にページを操作してDOMを確認しながら、実際のDOM構造に基づく信頼性の高いセレクターを決定してテストコードを生成する。
  Use when: (1) ユーザーが「E2Eテストを生成して」「テストコードを作って」と言う, (2) ユーザーが `/cyk-e2e-test-maker` を実行する。
argument-hint: '<ファイル名> <テスト内容> [URL]'
---

# E2Eテストコード生成スキル

PlaywrightのE2Eテストコードを、Playwright MCPで実際のDOM構造を確認しながら生成する。

## 引数の確認

`$ARGUMENTS` から以下を読み取る。未指定の項目はコンテキストから読み取る。不可能な場合はユーザーに確認する。

- **ファイル名**: 生成するテストファイル名（例: `login.spec.ts`）
- **テスト内容**: テストで検証する操作・シナリオの説明
- **テスト対象URL**: アクセスするURL
- **保存先**: 生成するテストファイルを保存するディレクトリ

## 手順

### Step 1: Playwright MCPでURLにアクセス

`browser_navigate` でテスト対象URLに移動する。接続できない場合はユーザーに報告して再接続を待ち、推測でテストコードを書かない。

### Step 2: DOM構造を確認してロケーターを決定

テスト内容の各検証対象について、以下の手順でロケーターを決定する。

1. 対象要素を含むコンテナ（ヘッダー・記事本文・フォームなど、ページレイアウト上の領域）を `browser_snapshot` の `target` で指定して構造を確認する
2. コンテナを `page.locator()` で取得し、その中の要素をセマンティックロケーター（`getByRole` / `getByLabel` / `getByText` / `getByPlaceholder` / `getByAltText` など）で特定する。コンテナは以下の基準で選定する
   - **採用する**: ページ内のエリア・領域を意味するクラス（例: `cg-GlobalHeader`、`cg-ArticleBody`）
   - **除外する**: レイアウト実装手段（`flex`、`grid`など）、状態クラス（`is-active`など）、コンポーネントスタイル（`btn`、`card`など）、広すぎるラッパー（`wrap`、`wrapper`、`app`）
3. `count()` を実行してヒット件数が1件であることを確認する。1件でない場合はユーザーに報告し、コンテナの見直しやロケーターの調整を行ってから再確認する

```typescript
const container = page.locator('<コンテナセレクター>');
const locator = container.getByRole('<role>', { name: '<text>', exact: true });

// 一意性の確認
const count = await locator.count();
```

**テキスト指定のルール:** 文字列リテラル + `exact: true` を必ず指定する。正規表現は使わない。ただしテキストの途中に改行が含まれる場合のみ正規表現を使う。

### Step 3: テストコードの生成と実行

決定したロケーターでテストコードを生成し、ファイルに保存する。

```ts
import { test, expect } from '@playwright/test';

test('<テスト内容>', async ({ page }) => {
  await page.goto('<テスト対象URL>');

  const container = page.locator('<コンテナセレクター>');
  await expect(
    container.getByRole('<role>', { name: '<text>', exact: true }),
  ).toBeVisible();
});
```

保存後、`npx playwright test <ファイル名>` を実行してテストがパスすることを確認する。失敗した場合はエラーメッセージを確認してロケーターを修正する。
