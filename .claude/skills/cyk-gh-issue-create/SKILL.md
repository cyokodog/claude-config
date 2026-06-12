---
name: cyk-gh-issue-create
description: 提案や計画を基に GitHub Issue を作成する。ポイント見積もり・重複チェック・Project への登録まで一貫して行う。
argument-hint: '[REPO_OWNER/REPO_NAME] [PROJECT_NAME] [PROJECT_ID] [POINTS_FIELD_ID]'
compatibility: gh CLI 認証済みであること（gh auth status が通ること）。
disable-model-invocation: true
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
2. なければ **未設定とする**（ポイント付与・Project 登録はスキップ）

#### ユーザーへの確認

Issue 作成前に以下の形式でパラメータをユーザーに提示し、OKをもらってから次のステップに進む：

```
## 実行パラメータ確認

| パラメータ | 値 | 取得元 |
|-----------|-----|--------|
| REPO_OWNER | xxx | git remote / 引数 / 未解決 |
| REPO_NAME | xxx | git remote / 引数 / 未解決 |
| PROJECT_NAME | xxx | 引数 / （未設定：Project登録スキップ） |
| PROJECT_ID | xxx | 引数 / （未設定：Project登録スキップ） |
| POINTS_FIELD_ID | xxx | 引数 / （未設定：ポイント付与スキップ） |
```

### 2. 提案・計画の分析

提供された提案や計画を分析してください。

- Issue の種別を以下の基準で判断してください：

  | ラベル | 用途 |
  |--------|------|
  | `bug` | バグ修正 |
  | `enhancement` | 新機能追加 |
  | `refactor` | リファクタリング |
  | `documentation` | ドキュメント変更 |
  | `test` | テスト追加・修正 |
  | `chore` | ビルド設定・依存関係など雑務 |

- 不明確な点や不足している情報がある場合は、ユーザーに確認を求めてください

### 3. Issue 内容の作成

`.github/ISSUE_TEMPLATE/` のテンプレートを読み込み、そのセクション構成に従って本文を作成してください。

- **Title**: 機能や修正内容を簡潔に表す日本語のタイトル。動詞止め（「〜する」「〜を作成する」）は使わず、名詞止め（「〜の作成」「〜の修正」「〜の追加」）にする
- **Body**: 種別に応じたテンプレートのセクションを埋める
  - bug（`bug_report.md`）: 概要 / 期待する動作と実際の動作 / 再現手順 / 環境
  - enhancement（`feature_request.md`）: 背景 / 解決したい問題 / ユースケース / 完了条件
  - refactor / test / chore / documentation（`feature_request.md` を流用）: 背景 / 目的 / 対象範囲 / 完了条件

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

### 6. Issue の作成

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

### 7. Project Item ID の取得

`PROJECT_ID` が設定されている場合のみ実施する。

```bash
cat <<GQL | gh api graphql -f query=-
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
```

- `data.repository.issue.projectItems.nodes[0].id` から ID を抽出してください
- `projectItems` が空（`nodes` が空配列）の場合、Issue がプロジェクトに追加されるまでの時間差が原因です。Issue 作成ステップには戻らず、数秒待ってからこのステップを再試行してください

### 8. Points フィールドの設定

`POINTS_FIELD_ID` が設定されている場合のみ実施する。

```bash
gh project item-edit \
  --id <ITEM_ID> \
  --field-id $POINTS_FIELD_ID \
  --number <POINTS_VALUE> \
  --project-id $PROJECT_ID
```
