---
name: cyk-e2e-test-maker-for-spa
description: >-
  SPA向けPlaywright形式のE2Eテストコードを生成するスキル。引数にファイル名・テスト名を受け取り、
  playwright codegenでユーザーがブラウザを操作して記録したコードを、テストを壊さないことを前提にClaudeが補正する。
  Playwright MCPで実際のDOMを確認しながらロケーターにコンテナを付与し、test.stepで処理のまとまりごとに構造化する。
  Use when: (1) ユーザーが「SPAのE2Eテストを生成して」「テストコードを作って」と言う, (2) ユーザーが `/cyk-e2e-test-maker-for-spa` を実行する。
argument-hint: '<ファイル名> <テスト名>'
---

# SPA向けE2Eテストコード生成スキル

## 引数

`$ARGUMENTS` から読み取る。不明なものはユーザーに確認する。

- **ファイル名**：生成するテストファイル名（例: `login.spec.ts`）
- **テスト名**：`test()` に付けるテスト名（例: `ログインできること`）
- **テスト対象URL**：会話から読み取る
- **保存先**：テストファイルを保存するディレクトリ。会話から読み取る

## Step 1: 記録

```bash
npx playwright codegen --output=<保存先>/tmp.spec.ts <テスト対象URL>
```

ユーザーにテストしたい操作を記録してもらい、終了したら `tmp.spec.ts` ができていることを確認する。

## Step 2: 記録したコードの実行

```bash
npx playwright test <保存先>/tmp.spec.ts
```

失敗したらユーザーに報告し、相談して直す。

## Step 3: コンテナの付与

`tmp.spec.ts` を `tmp-fixed.spec.ts` にコピーし、こちらを補正する。

- Playwright MCPでテスト対象URLを開く。接続できなければ中断して報告する
- `browser_take_screenshot` は使わない
- ロケーターの文字列は `tmp.spec.ts` の値をそのまま使う。name値の記号やアイコン文字も変えない

ロケーターを上から1つずつ、3-1〜3-5の順に処理する。SPAでは前の操作で表示される要素が多いため、まとめて処理しない。

### 3-1. 祖先要素のクラスの収集

記録されたロケーターで要素を取得し、目印を付けて、`html` までの祖先のタグ名とクラス名を集める。

```typescript
const path = await page
  .getByRole('button', { name: 'ページ追加' })
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

取得した要素が閉じかけのダイアログの中など、操作対象でない場合は、画面が落ち着くのを待って取り直す。

### 3-2. コンテナにするクラスの選定

プロジェクトでコンテナとして確定したクラスの一覧 `container-classes.md` を参照する。所在は、会話で把握していればそれを使い、なければE2Eテストのディレクトリ周辺を探す。

見つからなければ、作成するかをユーザーに確認する（保存先の既定は `.claude/e2e/container-classes.md`）。作成する場合は、ソースコードを調べてエリアを表すクラスを洗い出し、次の形式で保存する。作成しない場合は一覧なしで進む。

```markdown
# 既知のコンテナクラス一覧

| クラス名 | エリアの説明 |
| -------- | ------------ |
```

3-1で集めたクラスから、次の順で候補を選ぶ。候補が複数あれば、対象の要素に近い内側のものを採用する。

1. `container-classes.md` に載っているクラス
2. 載っていなければ、画面のエリアを表すクラス。採用したクラスは `container-classes.md` に追記する
   - 採用：サイドバー、メインエリア、ヘッダーなど、画面の領域を表すクラス
   - 除外：レイアウトの実装手段（`flex`、`grid`など）、状態（`is-active`など）、部品の見た目（`btn`、`card`など）、範囲が広すぎるラッパー（`wrap`、`wrapper`、`app`など）
3. どちらもなければコンテナを付けず、3-5に進む

### 3-3. ロケーターの書き換え

元のロケーターの先頭に `.locator()` でコンテナを足し、`tmp-fixed.spec.ts` に保存する。元のロケーターには手を加えない。

```typescript
await page
  .locator('.sidebar')
  .getByRole('button', { name: 'ページ追加' })
  .click();
```

### 3-4. 同一性の検証

コンテナで範囲を絞ると、`nth()` の番号がずれることがある。`nth()` を外したロケーターの候補から、目印を持つ要素の位置を求める。

```typescript
const index = await page
  .locator('.main-area')
  .getByText('ここに追加')
  .evaluateAll((els) =>
    els.findIndex((el) => el.hasAttribute('data-e2e-target')),
  );
```

- `nth()` がある場合：番号が違っていれば書き換える
- `nth()` がない場合：候補が1件で、位置が `0` であることを確かめる
- `-1` など想定外の結果なら、ユーザーに相談する

### 3-5. 補正したロケーターでの操作

目印を外し、書き換えたロケーターで操作して、画面を次の状態に進める。

```typescript
el.removeAttribute('data-e2e-target');
```

## Step 4: test.stepによる構造化

Step 3 がすべて終わってから行う（先に囲むとインデントが変わり、Step 3 の1行ずつの書き換えが崩れるため）。

各行の中身は変えず、`test.step()` で囲むだけにする。ネストは1段まで。

- テスト名に照らして、テストで確かめたい `expect()` を1つ見つける
  - 途中の状態を確認しているだけの `expect()`（準備が整ったことの確認など）は、これに当たらない
- その `expect()` の結果を生む操作から `expect()` までを本題、その前を準備、後ろを後片付けとしてまとめる
- ステップ名には、操作をなぞった説明ではなく、そのまとまりで何を確かめるのかを書く
  - 悪い例：`ボタンをクリックしてメニューを選択する`
  - 良い例：`部品を直下に複製できること`
- 準備と後片付けのステップ名には、頭に `準備:`、`後片付け:` を付ける

後続のステップで使う変数は、`test.step()` の外側で `let` 宣言する（ステップ内の `const` は後続から参照できない）。

## Step 5: テストファイルの生成

```bash
npx playwright test <保存先>/tmp-fixed.spec.ts
```

失敗したらユーザーに報告し、相談して直す。通ったら次を行い、完了を報告する。

- テスト名を引数のものに変える
- `tmp-fixed.spec.ts` を引数のファイル名にリネームする
- `tmp.spec.ts` を削除する
