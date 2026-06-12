---
name: cyk-gh-branch-create
description: GitHub Issue からブランチを作成し、実装計画を提示する。既存ブランチの命名規則を踏襲し、Issue の内容と実装を照合した計画をユーザーに提示する。
argument-hint: '[REPO_OWNER/REPO_NAME] [ISSUE番号またはURL] [BASE_BRANCH]'
compatibility: gh CLI 認証済み・git リポジトリ内であること（gh auth status が通ること）
disable-model-invocation: true
---

# cyk-gh-branch-create

## 手順

### 1. パラメータの解決

以下の優先順位でパラメータを解決し、**ブランチ作成前にユーザーに提示して確認を得る**。

#### REPO_OWNER / REPO_NAME

1. `$ARGUMENTS` に `REPO_OWNER/REPO_NAME` 形式で指定があればそれを使う
2. なければ作業ディレクトリの git リモート URL から取得する：
   ```bash
   git remote get-url origin
   ```
   - `github.com/OWNER/NAME` の形式からパースする
3. 取得できない場合はユーザーに確認する

#### ISSUE番号 / ISSUE URL（必須）

1. `$ARGUMENTS` に Issue 番号（例: `42`）または Issue URL（例: `https://github.com/OWNER/NAME/issues/42`）が指定されていればそれを使う
2. URL の場合は末尾の数字を Issue 番号として抽出する
3. 指定がない場合は **ユーザーに入力を求める**（Issue 番号または URL を尋ねる）

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
| ISSUE番号 | xxx | 引数 / ユーザー入力 |
| BASE_BRANCH | xxx | 引数 / GitHub デフォルト |
```

### 2. Issue 情報の取得

```bash
gh issue view <ISSUE番号> --repo "$REPO_OWNER/$REPO_NAME" --json number,title,labels,body
```

取得した情報から以下を把握する：
- Issue タイトル
- ラベル（bug / enhancement / documentation / refactor / test / chore / hotfix など）
- Issue 本文（完了条件・仕様の読み取りに使用）

### 3. ブランチ名の決定

#### 既存ブランチの命名規則を確認

```bash
gh api "repos/$REPO_OWNER/$REPO_NAME/branches" --jq '.[].name' | head -20
```

既存ブランチにプレフィックスのパターン（`fix/`、`feat/` など）が見られる場合は、その規則に倣ってブランチ名を生成する。

#### プレフィックスの判定（既存規則がない場合）

Issue のラベルとタイトルから以下の基準でプレフィックスを決定する：

| プレフィックス | 判断根拠 |
|---|---|
| `fix/` | `bug` ラベル、タイトルに「修正」「バグ」「fix」「bug」を含む |
| `feat/` | `enhancement` / `feature` ラベル、タイトルに「機能」「追加」「feat」を含む |
| `docs/` | `documentation` ラベル、タイトルに「ドキュメント」「docs」を含む |
| `refactor/` | `refactor` ラベル、タイトルに「リファクタ」「refactor」を含む |
| `test/` | `test` ラベル、タイトルに「テスト」「test」を含む |
| `hotfix/` | `hotfix` ラベル、タイトルに「緊急」「hotfix」を含む |
| `chore/` | 上記に該当しない場合 |

#### ブランチ名の生成

```
<プレフィックス>/#<Issue番号>-<Issueタイトルをスラッグ化>
```

スラッグ化のルール：
- 日本語はローマ字またはそのまま残す（簡潔に）
- スペース・特殊文字はハイフン（`-`）に置換
- 小文字に統一
- 長すぎる場合は適宜省略（50文字以内を目安）

例：`feat/#42-add-user-authentication`

### 4. ブランチ名の承認

提案するブランチ名をユーザーに提示し、OKをもらってから次のステップに進む。

```
## ブランチ名の提案

  <プレフィックス>/#<Issue番号>-<スラッグ>

このブランチ名で作成してよいですか？
変更する場合は希望のブランチ名をお知らせください。
```

### 5. ブランチの作成

```bash
git fetch origin
git checkout <BASE_BRANCH>
git pull origin <BASE_BRANCH>
git checkout -b <ブランチ名>
```

### 6. Issue 内容と実装の照合・計画提示

Issue の完了条件・仕様とカレントディレクトリのコードを照合し、実装計画を作成してユーザーに提示する。

- Issue 本文から完了条件・要件を読み取る
- 関連するファイル・ディレクトリ・関数を特定する
- 変更が必要な箇所とアプローチを整理する
- 注意点・考慮事項があれば記載する

提示形式：

```
## 実装計画

### Issue 要件サマリー
- <完了条件・要件を箇条書き>

### 変更対象
| ファイル | 変更内容 |
|---------|---------|
| path/to/file.ts | ～を追加・修正 |

### 実装アプローチ
1. ...
2. ...

### 注意点
- ...
```

### 7. 実装・動作確認の対話

実装計画をもとに実装を進め、ユーザーと対話しながら動作確認を行う。

- ユーザーの指示に従い実装・修正を繰り返す
- 必要に応じてテストや動作確認をユーザーに促す
- ユーザーから「問題なし」「PRして」など確認完了のサインが出たら次のステップへ進む

### 8. コミット確認

未コミットの変更がある場合、適切なコミット粒度とコミットメッセージを提示してユーザーに確認を得る。

```bash
git status
git diff
```

- 変更内容を把握し、論理的なまとまりでコミット単位を提案する
- 各コミットのメッセージを以下の形式で提示する：

```
## コミット提案

1. <コミットメッセージ>
   対象: path/to/file.ts, path/to/other.ts

2. <コミットメッセージ>
   対象: path/to/another.ts
```

ユーザーの承認後にコミットを実行する。修正希望があれば内容を調整してから再提示する。

### 9. PR 作成

最終的に適用された実装計画の内容を PR 本文に含めて PR を作成する。

```bash
gh pr create \
  --repo "$REPO_OWNER/$REPO_NAME" \
  --title "<Issue タイトル>" \
  --body "$(cat <<'EOF'
refs #<ISSUE番号>

## 実装計画

### Issue 要件サマリー
- <完了条件・要件を箇条書き>

### 変更対象
| ファイル | 変更内容 |
|---------|---------|
| path/to/file.ts | ～を追加・修正 |

### 実装アプローチ
1. ...
2. ...

### 注意点
- ...
EOF
)"
```

- PR タイトルは Issue タイトルをそのまま使う
- `refs #<ISSUE番号>` で Issue とリンクする
- 本文の実装計画は Step 7 の対話を経て最終確定した内容を反映する

### 10. マージ・クリーンアップ

PR 作成後、以下をまとめてユーザーに確認する：

```
PR をマージし、以下を実行してもよいですか？

1. PR をマージ
2. GitHub 上のブランチを削除
3. ローカルで <BASE_BRANCH> に切り替えて pull
```

ユーザーが yes の場合、以下を順に実行する：

```bash
gh pr merge --repo "$REPO_OWNER/$REPO_NAME" --squash --delete-branch
git checkout <BASE_BRANCH>
git pull origin <BASE_BRANCH>
```

- `--delete-branch` で GitHub 上のリモートブランチも同時に削除する
- マージ方式（`--squash` / `--merge` / `--rebase`）はリポジトリの運用に合わせて判断する。不明な場合は `--squash` をデフォルトとする
