# claude-config

Claude Code の設定（skills / agents）を管理するリポジトリ。

## 構成

**このリポジトリが実体、`~/.claude/` はシンボリックリンク**という関係になっている。

```
~/src/github.com/cyokodog/claude-config/.claude/skills/<name>/   ← 実体
~/.claude/skills/<name>  ->  上記                                 ← リンク

~/src/github.com/cyokodog/claude-config/.claude/agents/<name>.md ← 実体
~/.claude/agents/<name>.md  ->  上記                              ← リンク
```

リンクの粒度：

- **skills はディレクトリ単位**でリンクする（`SKILL.md` 個別ではない）
- **agents はファイル単位**でリンクする（1エージェント＝1 `.md`）

`~/.claude` 自体、`~/.claude/skills`、`~/.claude/agents` は実ディレクトリ。
その配下の各エントリだけがリンクになっている。

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
find ~/.claude/skills ~/.claude/agents -maxdepth 1 -type l ! -exec test -e {} \; -print

# repo にあるのに ~/.claude にリンクが無いものを検出
for d in ~/src/github.com/cyokodog/claude-config/.claude/skills/*/; do
  n=$(basename "$d"); [ -e ~/.claude/skills/"$n" ] || echo "未リンク: skills/$n"
done
for f in ~/src/github.com/cyokodog/claude-config/.claude/agents/*.md; do
  n=$(basename "$f"); [ -e ~/.claude/agents/"$n" ] || echo "未リンク: agents/$n"
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
