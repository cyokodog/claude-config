---
name: cyk-e2e-test-maker-for-spa
description: >-
  SPA向けPlaywright形式のE2Eテストコードを生成するスキル。引数にファイル名・テスト名・テスト対象URLを受け取り、
  playwright codegenでユーザーがブラウザを操作して記録したコードをClaudeが補正し、
  Playwright MCPで実行時のDOMを確認しながら信頼性の高いセレクターを決定してテストコードを生成する。
  Use when: (1) ユーザーが「SPAのE2Eテストを生成して」「テストコードを作って」と言う, (2) ユーザーが `/cyk-e2e-test-maker-for-spa` を実行する。
argument-hint: '<ファイル名> <テスト名> [URL]'
---

# SPA向けE2Eテストコード生成スキル

SPAのように操作のたびにDOMが動的に変化する画面向けに、`playwright codegen` と Playwright MCP を組み合わせてPlaywrightのE2Eテストコードを生成する。

## 引数の確認

`$ARGUMENTS` から以下を読み取る。未指定の項目はコンテキストから読み取る。不可能な場合はユーザーに確認する。

- **ファイル名**: 生成するテストファイル名（例: `login.spec.ts`）
- **テスト名**: 検証するシナリオのテスト名（例: `ログインできること`）
- **テスト対象URL**: アクセスするURL
- **保存先**: 生成するテストファイルを保存するディレクトリ

## 手順

### Step 1: codegenの実行

以下のコマンドをBashで実行する。

```bash
npx playwright codegen --output=<保存先>/tmp.spec.ts <テスト対象URL>
```

codegenが起動したら、ユーザーにブラウザでテストシナリオをすべて操作してもらい、完了したら終了してもらう。`<保存先>/tmp.spec.ts` が生成されたことを確認し、次のStepに進む。

### Step 2: tmp.spec.tsの実行と確認

Bashで以下を実行する。

```bash
npx playwright test <保存先>/tmp.spec.ts
```

- テストが成功したらユーザーに報告し、次のStepに進む
- エラーが発生した場合はユーザーに内容を報告し、ユーザーと`tmp.spec.ts` を修正して再実行する（Step 2を繰り返す）

### Step 3: コンテナの付与と一意性の検証

- **最重要：Playwright MCPでテスト対象URLに移動する。接続できない場合は処理を中断してユーザーに報告する。**
- **最重要：`browser_take_screenshot`によるスクショは禁止**

まず以下を実行して作業用ファイルを作成する。

```bash
cp <保存先>/tmp.spec.ts <保存先>/tmp-fixed.spec.ts
```

`tmp-fixed.spec.ts` の各ロケーターを一行ずつ読み取り、以下を行う。

#### 3-1. 対象要素の祖先クラスを収集し、マーキングする

例えば次のようなロケーターでUI操作するコードがあったとする。

```typescript
await page.getByRole('button', { name: ' ページ追加' }).click();
```

この場合は、ロケーター部分を `page.evaluate()` で実行し、

- 対象要素に `data-e2e-target="true"` を付与
- `html` までの祖先を辿って各要素の `classList` を収集する

```typescript
const path = await page
  .getByRole('button', { name: ' ページ追加' })
  .evaluate((domEl) => {
    domEl.setAttribute('data-e2e-target', 'true');
    const path = [];
    let current = domEl;
    while (current && current.tagName) {
      path.push({
        tag: current.tagName.toLowerCase(),
        classes: Array.from(current.classList),
      });
      current = current.parentElement;
    }
    return path;
  });
```

#### 3-2. コンテナクラスの推薦とユーザーの選定

収集したクラス名の中に、コンテキストウィンドウでエリアを示すクラス名として認識されているものがあれば、**それを採用しstep3-3に進む**

無い場合は、収集したクラス名から、以下の基準で「エリアを示す適切なコンテナクラス」を複数（2 or 3）選定する。

- **採用する**: ページ内のエリア・領域を意味するクラス
  （例: `header`, `footer`, `sidebar`, `nav`, `main`, `hero`, `content`, `container`）
- **除外する**:
  - レイアウト実装手段を示すクラス（例: `flex`, `grid`, `flex-row`, `flex-col`, `grid-cols-2`）
  - 状態・修飾クラス（例: `is-active`, `is-open`, `disabled`）
  - OS・環境フラグ（例: `os-mac`, `is-mobile`）
  - フォント・タイポグラフィ系（例: `font-sm`, `text-lg`）
  - コンポーネントスタイル（例: `btn`, `btn-primary`, `card`, `badge`）
  - 広すぎるラッパー（例: `wrap`, `wrapper`, `app`, `root`）

次のように、**どのクラスをコンテナにするかユーザーに選定してもらう。**

```
以下のクラスが見つかりました。どれをコンテナにしますか？ （複数選択可、番号で答えてください）
1. sidebar
2. sidebar__left
```

#### 3-3. ロケーターを書き換える

選定したコンテナクラスを先頭に付与し、`tmp-fixed.spec.ts` の元のロケーターを修正し、即座に保存する。

**変換前:**

```typescript
await page.getByRole('button', { name: ' ページ追加' }).click();
```

**変換後:**

```typescript
await page
  .locator('.sidebar')
  .getByRole('button', { name: ' ページ追加' })
  .click();
```

#### 3-4. 一意性と同一性の検証

調整したロケーターでヒット件数を取得し、

```typescript
const count = await page
  .locator('.sidebar')
  .getByRole('button', { name: ' ページ追加' })
  .count();
```

**調整したロケーターと件数をユーザーに報告する。ロケーターの文字列は `tmp.spec.ts` から読み取った値をそのままコードブロックで表示すること。絶対に書き直さない。（理由：name値に含まれる特殊文字や記号をテキスト生成時に誤って省略・変換するリスクがあるため）**

具体的には次のような変更は絶対にしないこと。

```
  .getByRole('button', { name: ' ページ追加' })
  ↓
  .getByRole('button', { name: ' ページ追加' })

```

次のように報告する。

```bash
以下の調整ロケーターで該当要素が ${count} 件見つかりました。
locator('.sidebar').getByRole('button', { name: ' ページ追加' })
```

**該当件数が1件以外の場合は、ユーザーとどう調整するか相談する。**1件の場合は次に同一性検証を行う。

調整したロケーターが指す要素に `data-e2e-target` 属性があるか検証する。

```typescript
const isSameElement = await page
  .locator('.sidebar')
  .getByRole('button', { name: ' ページ追加' })
  .evaluate((el) => el.hasAttribute('data-e2e-target'));
```

- **`true` の場合**: 同一要素であることが確認できたとして、以下のようにユーザーに報告し、

```bash
上記の調整ロケーターで調整前のロケーターと同一要素を取得できました
```

以下のよう**属性を除去して3-5へ進む。**

```typescript
await page
  .locator('.sidebar')
  .getByRole('button', { name: ' ページ追加' })
  .evaluate((el) => el.removeAttribute('data-e2e-target'));
```

- **`false` の場合**: 件数は1だが別の要素を指している。ユーザーにその旨を報告し、ロケーターの調整と、件数と属性一致の再チェックを再度行う。

#### 3-5. UI操作の実行

調整したロケーターでUI操作を実行する。

```typescript
await page
  .locator('.sidebar')
  .getByRole('button', { name: ' ページ追加' })
  .click();
```

操作が完了したら、以下のようにユーザーに伝える。

```bash
次のロケーターの調整に進みます。想定どうりの画面になってない場合はストップと言ってください。
```

**5秒まって回答がない場合は次のロケーターの調整に進む。未調整ロケーターがない場合は、Step4へ。**

### Step 4: テストファイルの生成

`tmp-fixed.spec.ts` の内容をもとに、以下を行う。

- テスト名を引数で指定されたものに変更する
- ファイル名を引数で指定されたものに変更して保存する
- `tmp.spec.ts` と `tmp-fixed.spec.ts` を削除する

完了をユーザーに報告する。
