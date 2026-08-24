---
name: cyk-gh-pr-create
description: 現在のブランチから GitHub PR を作成する。Issue タイトルに「PR」プレフィックスを付け、refs #番号・修正内容サマリーを本文に含める。
argument-hint: '[REPO_OWNER/REPO_NAME] [ISSUE番号またはURL] [BASE_BRANCH]'
compatibility: gh CLI 認証済み・git リポジトリ内であること（gh auth status が通ること）
disable-model-invocation: false
---

# cyk-gh-pr-create

## 手順

### 1. パラメータの解決

以下の優先順位でパラメータを解決し、**PR 作成前にユーザーに提示して確認を得る**。

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

- Issue タイトル（PR タイトルのベースに使用）
- Issue 本文（完了条件・仕様の読み取りに使用）

### 3. 変更内容の把握

カレントブランチと BASE_BRANCH の差分を確認して、修正内容のサマリーを作成する。

```bash
git log origin/<BASE_BRANCH>..HEAD --oneline
git diff origin/<BASE_BRANCH>...HEAD --stat
```

- コミット一覧と変更ファイルから修正内容を把握する
- Issue の完了条件・要件と照合し、対応状況を整理する

### 4. PR 内容の作成・提示

以下の形式で PR 内容を作成してユーザーに提示し、OKをもらってから次のステップに進む。

**タイトル**:

```
PR <Issue タイトル>
```

**本文**:

```
refs #<ISSUE番号>

## 修正内容サマリー

<変更内容を箇条書きで記載。何を・なぜ・どのように変更したかを簡潔に>

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| path/to/file.ts | ～を追加・修正 |
```

提示形式：

```
## PR 内容の確認

**タイトル**: PR <Issue タイトル>

**本文**:
refs #<ISSUE番号>

## 修正内容サマリー
- ...

## 変更ファイル
| ファイル | 変更内容 |
|---------|---------|
| ...

このPRを作成してよいですか？
変更する場合は修正点をお知らせください。
```

### 5. PR の作成

```bash
gh pr create \
  --repo "$REPO_OWNER/$REPO_NAME" \
  --base "<BASE_BRANCH>" \
  --title "PR <Issue タイトル>" \
  --body "$(cat <<'EOF'
refs #<ISSUE番号>

## 修正内容サマリー

<サマリー>

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| path/to/file.ts | ～を追加・修正 |
EOF
)"
```

- 作成後に PR の URL を出力する
