---
name: cyk-iterm-settings
description: カレントディレクトリに iTerm2 の背景色を割り当てる。~/.iterm-dir-colors を書き換え、次の cd で反映される。「このディレクトリに色を付けて」「背景色を変えて」「色の設定を見せて」と言われたら起動する。
argument-hint: '[色名またはhex（例: red / 2a0f0f）] [対象パス]（どちらも省略可）'
compatibility: iTerm2 + zsh。~/.zshrc に _iterm_bg_by_dir が定義済みであること。
disable-model-invocation: true
---

# cyk-iterm-settings

ディレクトリごとの iTerm2 背景色を設定する。対応表は `~/.iterm-dir-colors`。
`~/.zshrc` の `_iterm_bg_by_dir` が `cd` のたびにこのファイルを読み直すので、
**書き換えれば次の `cd` で反映される**（`source ~/.zshrc` は不要、他のタブにも効く）。

## 対応表の形式

```
<絶対パス>:<hex6>
```

- `#` 始まりの行と空行は無視
- 最長前方一致。サブディレクトリは親の色を継承する
- 特定のサブディレクトリだけ別色にしたい場合は、より長いパスの行を足せばそちらが勝つ
- **パスは必ず絶対パスで書く**。このファイルは sourced されないため `$HOME` や `~` は展開されない

## 実行形式

| 指定 | 動作 |
|---|---|
| `/cyk-iterm-settings` | 現在の対応表を一覧表示し、どうするか聞く |
| `/cyk-iterm-settings red` | カレントディレクトリに赤系を割り当て |
| `/cyk-iterm-settings 2a0f0f` | hex 直指定 |
| `/cyk-iterm-settings red ~/path/to` | パスを明示して割り当て |
| `/cyk-iterm-settings off` | カレントディレクトリの設定を削除 |

## 色の対応表

背景色なので**暗いトーンのみ**を使う。明るい色は Powerlevel10k のプロンプトが読めなくなる。
色名で指定された場合はこの表から引く。hex を直接指定された場合はそのまま使うが、
明るすぎる場合（後述の判定）は警告した上で確認を取る。

| 色名 | hex | | 色名 | hex |
|---|---|---|---|---|
| red / 赤 | `2a0f0f` | | green / 緑 | `0f2a14` |
| blue / 青 | `0f1f2a` | | yellow / 黄 | `2a250f` |
| purple / 紫 | `1a0f22` | | cyan / 水 | `0f2a2a` |
| orange / 橙 | `2a1f0f` | | pink / 桃 | `2a0f1f` |
| gray / 灰 | `1c1c1c` | | brown / 茶 | `2a1f0f` |

明るさ判定: hex を RGB に分解し `0.299R + 0.587G + 0.114B > 80` なら「明るすぎる」と警告する。

## 手順

### 1. 対象パスと色を決める

- 対象パス: 引数で指定されていればそれ、なければ**カレントディレクトリ**（`pwd -P` でシンボリックリンクを解決した絶対パス）
- 色: 引数の色名/hex。引数が無ければ現在の設定を表示して何色にするか聞く

### 2. 対応表を書き換える

`~/.iterm-dir-colors` を読み、同じパスの行があれば**上書き**、なければ**追記**する。
ファイルが無い場合はヘッダコメント付きで新規作成する。

```bash
# 例: 上書き or 追記
python3 - <<'EOF'
import io, os
f = os.path.expanduser("~/.iterm-dir-colors")
path, color = "<対象パス>", "<hex>"
lines = io.open(f, encoding="utf-8").read().splitlines() if os.path.exists(f) else [
    "# ディレクトリごとの iTerm2 背景色",
    "# 形式: <絶対パス>:<hex6>   （# 始まりと空行は無視）",
    "# 最長前方一致。サブディレクトリは親の色を継承する。",
]
out, done = [], False
for ln in lines:
    if ln.strip() and not ln.lstrip().startswith("#") and ln.rsplit(":", 1)[0] == path:
        if not done:
            out.append(f"{path}:{color}"); done = True
        continue
    out.append(ln)
if not done:
    out.append(f"{path}:{color}")
io.open(f, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
EOF
```

`off` の場合は該当行を削除するだけ（追記はしない）。

### 3. 反映を伝える

書き換え後、必ずこう伝える:

- **他のタブ・次回以降**: 次に `cd` した時点で自動的に反映される（何もしなくてよい）
- **今開いているタブで今すぐ見たい場合**: そのタブで `cd .` を実行する（同じディレクトリでも `chpwd` が走るので即反映される）

注意: このスキルの Bash 実行の出力はユーザーの端末には届かない。
`printf` でエスケープシーケンスを撃っても**ユーザーの画面の色は変わらない**ので、
「即座に色が変わりました」とは言わないこと。上記の `cd .` を案内する。

### 4. 結果を表示

書き換え後の対応表を、パスを `~/` 表記にして一覧で見せる。

## 一覧表示

引数なしで呼ばれた場合、および書き換え後の結果表示（手順4）で使う。
`~/.iterm-dir-colors` を読んで整形する。存在しないディレクトリには印を付ける。

```bash
python3 - <<'EOF'
import io, os
HOME = os.path.expanduser("~")
NAMES = {"2a0f0f":"red","0f2a14":"green","0f1f2a":"blue","2a250f":"yellow",
         "1a0f22":"purple","0f2a2a":"cyan","2a1f0f":"orange/brown","2a0f1f":"pink","1c1c1c":"gray"}
f = os.path.expanduser("~/.iterm-dir-colors")
rows = []
if os.path.exists(f):
    for ln in io.open(f, encoding="utf-8").read().splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        path, color = ln.rsplit(":", 1)
        disp = path.replace(HOME, "~", 1) if path.startswith(HOME) else path
        warn = "" if os.path.isdir(path) else "  ← ディレクトリ無し"
        rows.append((disp, color, NAMES.get(color.lower(), "-"), warn))
if not rows:
    print("(設定なし)")
else:
    w = max(len(r[0]) for r in rows)
    for disp, color, name, warn in sorted(rows):
        print(f"{disp:<{w}}  #{color}  {name}{warn}")
EOF
```

表示後、引数なし呼び出しの場合は「どのディレクトリに何色を設定するか」を聞く。

補足として、現在のディレクトリが継承で色を得ている場合（自身の行は無いが親の行に一致する場合）は
「このディレクトリは <親パス> の設定を継承中」と併記する。
