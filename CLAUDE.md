# claude-config

Claude Code の設定（グローバルの CLAUDE.md / rules / skills / agents）と、プロジェクトをまたぐナレッジ（`knowledge/`）を管理するリポジトリ。

## 構成

**このリポジトリが実体、`~/.claude/` はシンボリックリンク**という関係になっている。

```
~/src/github.com/cyokodog/claude-config/.claude/skills/<name>/   ← 実体
~/.claude/skills/<name>  ->  上記                                 ← リンク

~/src/github.com/cyokodog/claude-config/.claude/agents/<name>.md ← 実体
~/.claude/agents/<name>.md  ->  上記                              ← リンク
```

```
~/src/github.com/cyokodog/claude-config/.claude/CLAUDE.md         ← 実体（全プロジェクト共通の指示）
~/.claude/CLAUDE.md  ->  上記                                      ← リンク

~/src/github.com/cyokodog/claude-config/.claude/rules/<name>.md  ← 実体（プロジェクトをまたぐルール）
~/.claude/rules/<name>.md  ->  上記                               ← リンク
```

リンクの粒度：

- **skills はディレクトリ単位**でリンクする（`SKILL.md` 個別ではない）
- **agents / rules はファイル単位**でリンクする（1ファイル＝1 `.md`）
- **CLAUDE.md はファイル1つ**をリンクする

`~/.claude` 自体、`~/.claude/skills`、`~/.claude/agents`、`~/.claude/rules` は実ディレクトリ。
その配下の各エントリだけがリンクになっている。

`knowledge/` はリンクしない（自動では読み込まれない）。`rules/knowledge-index.md` が目次 `knowledge/README.md` の場所を教え、必要なときに読ませる。
ナレッジとルールの使い分けは `rules/personal-projects.md` を参照。

### rules の書き方

- 毎回読み込まれるので短く保つ。1 テーマ 1 ファイル
- 特定のファイルを触るときだけ効けばよいものは、先頭の frontmatter の `paths:` で絞る（例: `rules/cyk-design-system.md`）
- このリポジトリの中で作業すると、`.claude/CLAUDE.md` と `.claude/rules/` はプロジェクトの指示としても読み込まれる（`~/.claude/` 側と同じ内容が二重に入るだけで害はない）

## 鉄則：追加・リネーム・削除したら必ずリンクを張り直す

**リポジトリ側を変更しただけでは Claude Code に反映されない。**
`~/.claude/` 側のリンクを同時にメンテすること。以下は毎回実行する。

### skill / agent を新規追加したとき

```bash
REPO=~/src/github.com/cyokodog/claude-config/.claude

# skill（ディレクトリ単位）
ln -s "$REPO/skills/<name>" ~/.claude/skills/<name>

# agent（ファイル単位）
ln -s "$REPO/agents/<name>.md" ~/.claude/agents/<name>.md

# rule（ファイル単位）
ln -s "$REPO/rules/<name>.md" ~/.claude/rules/<name>.md
```

### リネームしたとき

古いリンクを消してから新しいリンクを張る。**古いリンクを消し忘れると、
同じ内容のスキルが2つ存在することになり自動起動が競合する。**

```bash
rm ~/.claude/skills/<old-name>
ln -s "$REPO/skills/<new-name>" ~/.claude/skills/<new-name>
```

なお `git mv` でディレクトリをリネームする際、そのディレクトリの追跡対象が
1ファイルだけだと**ファイルに畳まれることがある**。`git ls-files -s` でモードを確認し、
`100644`（実ファイル）になっていること、`120000`（シンボリックリンク）で
記録されていないことを確認する。

### 削除したとき

```bash
rm ~/.claude/skills/<name>      # リンクを消す（実体ではない）
```

### 作業後の検証（必ず実行）

```bash
# 壊れたリンクが無いこと
find ~/.claude/skills ~/.claude/agents ~/.claude/rules -maxdepth 1 -type l ! -exec test -e {} \; -print
[ -L ~/.claude/CLAUDE.md ] && [ -e ~/.claude/CLAUDE.md ] || echo "CLAUDE.md がリンクになっていない"


# repo にあるのに ~/.claude にリンクが無いものを検出
for d in ~/src/github.com/cyokodog/claude-config/.claude/skills/*/; do
  n=$(basename "$d"); [ -e ~/.claude/skills/"$n" ] || echo "未リンク: skills/$n"
done
for f in ~/src/github.com/cyokodog/claude-config/.claude/agents/*.md; do
  n=$(basename "$f"); [ -e ~/.claude/agents/"$n" ] || echo "未リンク: agents/$n"
done
for f in ~/src/github.com/cyokodog/claude-config/.claude/rules/*.md; do
  n=$(basename "$f"); [ -e ~/.claude/rules/"$n" ] || echo "未リンク: rules/$n"
done
```

両方とも何も出力されなければ正常。

## 注意

- `~/.claude/skills/` にはこのリポジトリ以外由来のものも同居している
  （`Takazudo/claude-resources` へのリンク、Cloudflare 公式系の実ディレクトリなど）。
  **cyk- 系以外には触らない。**
- `~/.claude/` 配下を `rm -rf` する前に、それがリンクか実体かを必ず確認する。
  リンク先を消すと実体を失う。
- ファイル名は `SKILL.md`（大文字）。
