---
name: cyk-gh-issue-create
description: 提案や計画を基に GitHub Issue を作成する。ポイント見積もり・重複チェック・Project への登録まで一貫して行う。
argument-hint: '[REPO_OWNER/REPO_NAME] [PROJECT_NAME] [PROJECT_ID] [POINTS_FIELD_ID]'
compatibility: gh CLI 認証済みであること（gh auth status が通ること）。
disable-model-invocation: false
---

# cyk-gh-issue-create

## 手順

### 1. パラメータの解決

以下の優先順位でパラメータを解決し、**Issue 作成前にユーザーに提示して確認を得る**。

#### REPO_OWNER / REPO_NAME

1. `$ARGUMENTS` に `REPO_OWNER/REPO_NAME` 形式で指定があればそれを使う
2. なければ作業ディレクトリの git リモート URL から取得する：

   ```bash
   git remote get-url origin
   ```

   - `github.com/OWNER/NAME` の形式からパースする

3. 取得できない場合はユーザーに確認する

#### PROJECT_NAME / PROJECT_ID / POINTS_FIELD_ID

1. `$ARGUMENTS` に指定があればそれを使う
2. なければ `gh` から自動検出する：

   ```bash
   # PROJECT_NAME / PROJECT_ID
   gh project list --owner "$REPO_OWNER" --format json
   ```

   - `title` が `REPO_NAME` と**完全一致**する project を採用する
   - 部分一致は使わない（owner 配下にはリポジトリと無関係な project が多数あり、誤検出するため）
   - `number` と `id` を控える

   ```bash
   # POINTS_FIELD_ID
   gh project field-list <NUMBER> --owner "$REPO_OWNER" --format json
   ```

   - `name` が `Points` のフィールドの `id` を採用する

3. 自動検出でも見つからなければ **未設定とする**（ポイント付与・Project 登録はスキップ）

#### ユーザーへの確認

Issue 作成前に以下の形式でパラメータをユーザーに提示し、OKをもらってから次のステップに進む：

```
## 実行パラメータ確認

| パラメータ | 値 | 取得元 |
|-----------|-----|--------|
| REPO_OWNER | xxx | git remote / 引数 / 未解決 |
| REPO_NAME | xxx | git remote / 引数 / 未解決 |
| PROJECT_NAME | xxx | 引数 / 自動検出 / （未設定：Project登録スキップ） |
| PROJECT_ID | xxx | 引数 / 自動検出 / （未設定：Project登録スキップ） |
| POINTS_FIELD_ID | xxx | 引数 / 自動検出 / （未設定：ポイント付与スキップ） |
```

### 2. 提案・計画の分析

提供された提案や計画を分析してください。

- Issue の種別を以下の基準で判断してください：

  | ラベル          | 用途                         |
  | --------------- | ---------------------------- |
  | `bug`           | バグ修正                     |
  | `enhancement`   | 新機能追加                   |
  | `refactor`      | リファクタリング             |
  | `documentation` | ドキュメント変更             |
  | `test`          | テスト追加・修正             |
  | `chore`         | ビルド設定・依存関係など雑務 |

- 不明確な点や不足している情報がある場合は、ユーザーに確認を求めてください

### 3. Issue 内容の作成

Issue 本文の主役は **「こういう問題がある」「こういうことを実現したい」「その時点でわかっている前提」** の3つ。読者にこれが伝わることが最も大事。

**概要と詳細を混ぜない。** 概要の節にファイルパス・行番号・コード片を書かない。読者が「何を実現したいのか」を掴む前に実装詳細に突き落とさないこと。

**実装方針・手順は Issue 本文に書かない。** それは実装計画md（`docs/issues/<N>/`、`cyk-impl-plan-create` の役割）に書く。Issue 本文に手順を書くと二重管理になり、どちらが正か分からなくなる。

- **Title**: 機能や修正内容を簡潔に表す日本語のタイトル。動詞止め（「〜する」「〜を作成する」）は使わず、名詞止め（「〜の作成」「〜の修正」「〜の追加」）にする
- **Body**: セクション構成は以下で決める
  - `.github/ISSUE_TEMPLATE/` が**ある**場合 → そのテンプレートのセクション構成に従う
  - `.github/ISSUE_TEMPLATE/` が**ない**場合 → 種別によらず次の既定構成を使う

既定の構成：

```markdown
## 概要

<何が問題で、何を実現したいか。ファイルパス・行番号・コード片は書かない>

## 前提

<調査で分かっていること。ここで初めて具体名を出してよい。無ければ節ごと省略>

## 完了条件

- [ ] <条件>
```

bug の場合は `## 概要` に「期待する動作と実際の動作」「再現手順」「環境」を含める。

### 4. ポイントの見積もり

`POINTS_FIELD_ID` が設定されている場合のみ実施する。

タスクの価値・複雑さをポイント（フィボナッチ: 1, 2, 3, 5, 8）で見積もってください。

| ポイント | 基準                                         |
| -------- | -------------------------------------------- |
| 1        | 簡単なタスク（軽微な依頼、テキスト変更など） |
| 2        | 小規模な変更（単純なコード修正など）         |
| 3        | テストを伴うコード変更、または中程度の複雑さ |
| 5        | 高い価値または複雑さを持つタスク             |
| 8        | 大規模または非常に複雑なタスク               |

### 5. 重複チェック

Issue を作成する前に、同名の Issue が既に存在しないか確認してください。

```bash
gh issue list --repo "$REPO_OWNER/$REPO_NAME" --search '"<タイトル>" in:title' --state open --json number,title --limit 1
```

- `in:title` を指定することで、本文・コメントを除くタイトルのみを検索対象にします
- `--limit 1` で最新の 1 件のみ取得します
- 結果が存在する場合は、作成をスキップして既存の Issue 番号を返してください
- 結果が空の場合のみ、次のステップ（Issue 作成）に進んでください

### 6. Issue 内容の確認

作成前に、Step 3〜5 で決定した内容を以下の形式でユーザーに提示し、**OK をもらってから次のステップに進む**。

```
## 作成する Issue

**Repo**: OWNER/NAME
**Title**: <タイトル>
**Labels**: ai-generated, <種別>
**Points**: <ポイント>（未設定の場合は「スキップ」）
**Project**: <PROJECT_NAME>（未設定の場合は「スキップ」）

---

<本文（Markdown そのまま）>
```

- ユーザーから修正指示があった場合は反映し、再度提示して確認を得る
- 承認を得るまで `gh issue create` を実行しない

### 7. Issue の作成

`PROJECT_NAME` が設定されている場合は `--project` を付与し、未設定の場合は省略する。

```bash
gh issue create \
  --repo "$REPO_OWNER/$REPO_NAME" \
  --title "<タイトル>" \
  --body "$(cat <<'EOF'
<本文>
EOF
)" \
  --label "ai-generated" \
  --label "<bug / enhancement / refactor / documentation / test / chore のいずれか>" \
  [--project "$PROJECT_NAME"]  # PROJECT_NAME が設定されている場合のみ
```

- `--label` の種別は Step 2 で判断した種別を設定してください
- Body は適切にフォーマットしてください（改行など）
- 出力された URL から Issue 番号を取得してください

### 8. Project Item ID の取得

`PROJECT_ID` が設定されている場合のみ実施する。

```bash
gh api graphql -f query="$(cat <<GQL
{
  repository(owner: "$REPO_OWNER", name: "$REPO_NAME") {
    issue(number: <ISSUE_NUMBER>) {
      projectItems(first: 1) {
        nodes {
          id
        }
      }
    }
  }
}
GQL
)"
```

- ヒアドキュメントは `-f query="$(cat <<GQL ... GQL)"` の形で渡す。`-f query=-` は stdin として解釈されず、`-` がそのままクエリ本体として送られて失敗する
- `<<GQL` はクォートしない（`$REPO_OWNER` / `$REPO_NAME` を展開させるため）
- `data.repository.issue.projectItems.nodes[0].id` から ID を抽出してください
- `projectItems` が空（`nodes` が空配列）の場合、Issue がプロジェクトに追加されるまでの時間差が原因です。Issue 作成ステップには戻らず、数秒待ってからこのステップを再試行してください

### 9. Points フィールドの設定

`POINTS_FIELD_ID` が設定されている場合のみ実施する。

```bash
gh project item-edit \
  --id <ITEM_ID> \
  --field-id $POINTS_FIELD_ID \
  --number <POINTS_VALUE> \
  --project-id $PROJECT_ID
```
