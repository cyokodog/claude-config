---
name: cyk-gh-pr-review
description: Issue に対する PR 相当の変更をレビューする。Issue 要件の充足確認とコード品質チェックを行い、結果を出力する。
argument-hint: '[REPO_OWNER/REPO_NAME] [ISSUE番号またはURL] [BASE_BRANCH]'
compatibility: gh CLI 認証済み・git リポジトリ内であること（gh auth status が通ること）
disable-model-invocation: false
---

# cyk-gh-pr-review

## 手順

### 1. パラメータの解決

以下の優先順位でパラメータを解決し、**レビュー開始前にユーザーに提示して確認を得る**。

#### REPO_OWNER / REPO_NAME

1. `$ARGUMENTS` に `REPO_OWNER/REPO_NAME` 形式で指定があればそれを使う
2. なければ作業ディレクトリの git リモート URL から取得する：

   ```bash
   git remote get-url origin
   ```

   - `github.com/OWNER/NAME` の形式からパースする

3. 取得できない場合はユーザーに確認する

#### ISSUE番号 / ISSUE URL

1. `$ARGUMENTS` に Issue 番号（例: `42`）または Issue URL（例: `https://github.com/OWNER/NAME/issues/42`）が指定されていればそれを使う
2. URL の場合は末尾の数字を Issue 番号として抽出する
3. 指定がない場合、カレントブランチ名から Issue 番号を推測する（例: `feat/#42-xxx` → `42`）
4. 推測できない場合は **ユーザーに入力を求める**

#### BASE_BRANCH

1. `$ARGUMENTS` に指定があればそれを使う
2. なければ GitHub のデフォルトブランチを取得する：
   ```bash
   gh repo view "$REPO_OWNER/$REPO_NAME" --json defaultBranchRef --jq '.defaultBranchRef.name'
   ```

#### ユーザーへの確認

パラメータ解決後、以下の形式で提示し、OKをもらってから次のステップに進む：

```
## 実行パラメータ確認

| パラメータ | 値 | 取得元 |
|-----------|-----|--------|
| REPO_OWNER | xxx | git remote / 引数 |
| REPO_NAME | xxx | git remote / 引数 |
| ISSUE番号 | xxx | 引数 / ブランチ名から推測 / ユーザー入力 |
| BASE_BRANCH | xxx | 引数 / GitHub デフォルト |
```

### 2. Issue 情報の取得

```bash
gh issue view <ISSUE番号> --repo "$REPO_OWNER/$REPO_NAME" --json number,title,body,labels
```

取得した情報から以下を把握する：

- Issue タイトル
- Issue 本文に含まれる完了条件・要件・仕様
- ラベル（bug / enhancement / refactor など）

完了条件が明示されていない場合は、Issue 本文全体から要件を読み取って一覧化する。

### 3. 差分の取得

```bash
git fetch origin
git diff origin/<BASE_BRANCH>...HEAD
git log origin/<BASE_BRANCH>..HEAD --oneline
git diff origin/<BASE_BRANCH>...HEAD --stat
```

- コミット一覧・変更ファイル一覧・コードの差分を把握する
- 差分が大きい場合はファイル単位で順に読む

### 4. Issue 要件の充足確認

Step 2 で把握した要件・完了条件を一覧化し、Step 3 の差分と照合して各要件の充足状況を判定する。

判定基準：

| 記号 | 意味 |
|------|------|
| ✅ | 差分に実装が確認できる |
| ❌ | 実装が見当たらない・明らかに未対応 |
| ⚠️ | 部分的に実装されているが不完全、または確認しきれない |

また、Issue のスコープ外の変更（要件に関係のない変更）が含まれている場合は別途指摘する。

### 5. コードレビュー

差分に対して以下の観点でレビューを行う。

#### HIGH（必ず確認する）

**バグ・ロジックエラー**

- 条件式の誤り（逆条件、境界値ミスなど）
- null / undefined の未チェック
- 非同期処理の誤り（await 漏れ、競合状態など）
- ループの誤り（off-by-one など）
- API の誤った使い方

**セキュリティ**

- XSS（ユーザー入力の未サニタイズ）
- SQL / コマンドインジェクション
- 機密情報のハードコード（APIキー、パスワードなど）
- 入力バリデーションの欠如（システム境界での未検証）
- 認証・認可の抜け

#### MEDIUM（気になる点があれば指摘する）

**コードの複雑さ・重複**

- DRY 違反（同じロジックが複数箇所に存在する）
- 関数・メソッドが長すぎる（処理が多すぎる）
- ネストが深すぎて読みにくい
- マジックナンバー・マジック文字列

**型安全性（TypeScript の場合）**

- `any` の不適切な使用
- 型アサション（`as`）の乱用
- 型定義の不正確さ

#### LOW（オプションで指摘する）

**可読性・保守性**

- 変数名・関数名が意図を表していない
- コードの配置・ファイル構成が不自然
- 不要なコメント・コードの残骸（デバッグ用 console.log など）

### 6. レビュー結果の出力

以下の形式でレビュー結果を出力する。

```
## レビュー結果

### Issue 要件の充足確認

| 要件 | 状態 | 備考 |
|------|------|------|
| <要件1> | ✅ | <該当ファイル・行など> |
| <要件2> | ❌ | <未実装の理由・確認箇所> |
| <要件3> | ⚠️ | <不完全な点> |

<スコープ外の変更がある場合>
#### スコープ外の変更
- <ファイル>: <変更内容と懸念点>

---

### コードレビュー指摘

#### HIGH
- `path/to/file.ts:42` — <問題の説明。なぜ問題か・どう直すかを簡潔に>
- `path/to/file.ts:87` — <問題の説明>

#### MEDIUM
- `path/to/file.ts:15` — <問題の説明>

#### LOW
- `path/to/file.ts:30` — <問題の説明>

<指摘がないカテゴリは省略する>

---

### 総評

**判定**: マージ可 / 要修正

<2〜3文で総合的なコメント。要件の充足状況・主な懸念点・修正が必要な場合はその優先度を記載>
```

指摘がないカテゴリ（HIGH / MEDIUM / LOW）は出力を省略する。
問題が何もない場合は「指摘なし」と明記する。
