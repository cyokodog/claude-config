---
name: cyk-iterm-settings
description: カレントディレクトリに iTerm2 の背景色を割り当てる。~/.iterm-dir-colors を書き換え、次の cd で反映される。「このディレクトリに色を付けて」「背景色を変えて」「色の設定を見せて」と言われたら起動する。
argument-hint: '[色名またはhex（例: red / 2a0f0f）＝ピッカーの初期色] [対象パス]（どちらも省略可）'
compatibility: iTerm2 + zsh。~/.zshrc に _iterm_bg_by_dir が定義済みであること。色決めは Artifact のピッカーページ（要 Claude in Chrome）を使う。
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
| `/cyk-iterm-settings` | 現在の対応表を一覧表示し、どうするか聞く（ピッカーは出さない） |
| `/cyk-iterm-settings 色をつけて` | カレントディレクトリ向けにピッカーを開く |
| `/cyk-iterm-settings red` | 赤を**初期色**にしてピッカーを開く |
| `/cyk-iterm-settings 2a0f0f` | hex を**初期色**にしてピッカーを開く |
| `/cyk-iterm-settings red ~/path/to` | パスを明示してピッカーを開く |
| `/cyk-iterm-settings off` | カレントディレクトリの設定を削除（ピッカーは出さない） |

色名・hex は**最終値ではなく初期値**。ユーザーはピッカー上で微調整して決定する。
ピッカーを経由せず即確定したい場合は、ユーザーがそう言ったときだけ従来どおり直接書き込む。

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

### 1. 対象パスと初期色を決める

- 対象パス: 引数で指定されていればそれ、なければ**カレントディレクトリ**（`pwd -P` でシンボリックリンクを解決した絶対パス）
- 初期色: 引数の色名/hex を上の対応表から引く。引数が無ければ、対象パスの現在の設定色、それも無ければ `1c1c1c`

`off` の場合はここで手順4（削除）へ飛ぶ。引数なしの素の呼び出しは「一覧表示」だけ行い、
ピッカーは出さずにどうするか聞く。

### 2. ピッカーを publish して開く

Artifact ツールで色決めページを publish し、ユーザーの Chrome で開く。

**2-1. アセットをスクラッチパッドへコピーしてトークンを置換する。**
Artifact ツールは作業ディレクトリかスクラッチパッド配下のファイルしか publish できないため、
`~/.claude/skills/` から直接は publish できない。必ずコピーしてから使う。

```bash
# <scratchpad> は環境情報で示されたスクラッチパッドの絶対パス
python3 - <<'EOF'
import io, os
src = os.path.expanduser("~/.claude/skills/cyk-iterm-settings/assets/picker.html")
dst = "<scratchpad>/iterm-bg-picker.html"
HOME = os.path.expanduser("~")

target  = "<対象パスの絶対パス>"
initial = "#<初期色hex6>"

display = target.replace(HOME, "~", 1) if target.startswith(HOME) else target
# プロンプト表示は p10k 風に中間ディレクトリを1文字へ短縮する
parts = display.split("/")
prompt_dir = "/".join([p[:1] if p not in ("~",) else p for p in parts[:-1]] + [parts[-1]])

s = io.open(src, encoding="utf-8").read()
for k, v in {
    "__TARGET_PATH__": target,
    "__TARGET_DISPLAY__": display,
    "__TARGET_BASENAME__": os.path.basename(target) or target,
    "__PROMPT_DIR__": prompt_dir,
    "__INITIAL_HEX__": initial,
}.items():
    s = s.replace(k, v)
assert "__" not in s.replace("__proto__", ""), "未置換のトークンが残っている"
io.open(dst, "w", encoding="utf-8").write(s)
print(dst)
EOF
```

**2-2. publish する。** `capabilities: {"db": {}}` を必ず渡す（ページが決定値を保存するのに使う）。
`favicon` は初回のみ。毎回新しく publish してよい（URLの使い回しはしない。
古い決定値が残っていると取り違えるため、毎回まっさらな db から始めるほうが安全）。

**2-3. Chrome で開く。** `tabs_context_mcp` → `navigate` で publish された URL を開く。
**タブは閉じない**（ユーザーが操作中のため）。

**2-4. ユーザーに伝える。** ピッカーで色を調整し、「この色に決定」を押してから
「決定した」と言ってもらうよう案内する。hex を口頭で伝える必要はないことも添える。

publish や Chrome 起動に失敗した場合は、ピッカーを諦めて
**従来どおり色名/hex を直接書き込む方式にフォールバックする**（ユーザーにその旨を伝える）。

### 3. 決定値を読んで反映する

ユーザーが「決定した」と言ったら、Artifact ツールの `read_db` で読む。

- `action: "read_db"`、`url`: 手順2で publish した URL
- `db_op: "get"`、`collection: "choices"`、`doc_id: "iterm-bg"`

**読んだ値は必ず検証してから使う**（取り違え防止）:

1. ドキュメントが存在しない → 「まだ決定が保存されていません」と伝え、書き込まない
2. `data.path` が手順1の対象パスと**不一致** → 別ディレクトリ向けの古い決定。書き込まない
3. `data.hex` が `^[0-9a-f]{6}$` に一致しない → 書き込まない

検証を通ったら `data.hex` を手順4で書き込む。`data.luminance` が 80 を超えていれば警告を添える。

### 4. 対応表を書き換える

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

### 5. 反映を伝える

書き換え後、必ずこう伝える:

- **他のタブ・次回以降**: 次に `cd` した時点で自動的に反映される（何もしなくてよい）
- **今開いているタブで今すぐ見たい場合**: そのタブで `iterm-bg-reload` を実行する
  （`cd .` では効かない。zsh の `chpwd` は実際にディレクトリが変わったときしか発火しないため）

注意: このスキルの Bash 実行の出力はユーザーの端末には届かない。
`printf` でエスケープシーケンスを撃っても**ユーザーの画面の色は変わらない**ので、
「即座に色が変わりました」とは言わないこと。上記の `iterm-bg-reload` を案内する。

### 6. 結果を表示

書き換え後の対応表を、パスを `~/` 表記にして一覧で見せる。

## 一覧表示

引数なしで呼ばれた場合、および書き換え後の結果表示（手順6）で使う。
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
