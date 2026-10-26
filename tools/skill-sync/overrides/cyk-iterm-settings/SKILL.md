---
name: cyk-iterm-settings
description: カレントディレクトリに iTerm2 の背景色を割り当てる。~/.iterm-dir-colors を書き換え、次の cd で反映される。「このディレクトリに色を付けて」「背景色を変えて」「色の設定を見せて」と言われたら起動する。
---

# cyk-iterm-settings

前提：iTerm2とzsh、既存の `_iterm_bg_by_dir` を使用する。色名・hex・対象パスはユーザーの入力から解決する。このスキルの自動起動禁止は `agents/openai.yaml` に維持する。

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

### 2. ローカルのピッカーを開く

Codex版は外部のArtifact公開・データベースを使わない。このスキルに同梱された `scripts/picker_server.py` が、ローカルのページと決定値保存を提供する。色設定ファイルはサーバー自身では変更しない。

1. このスキルを読み込んだ実際のディレクトリを基準に `scripts/picker_server.py` を特定する。Claude版の原本側のアセットへ差し替えない。
2. スクラッチパッド配下の、まだ存在しない新しいセッションディレクトリを指定し、サーバーを起動する。対象パスなどの引数は適切にシェルクォートする。

```bash
python3 <このスキルのディレクトリ>/scripts/picker_server.py \
  --target '<対象ディレクトリの絶対パス>' \
  --initial '<初期色hex6>' \
  --session-dir '<scratchpad内の新しいセッションディレクトリ>'
```

3. サーバーは起動結果としてURLと保存先をJSONで返し、同じ情報を `session.json` に保存する。実行ツールの継続セッションで稼働させ、結果が決まるまで止めない。ポート待受けなどで承認が必要なら、環境の承認手続きを使う。
4. `~/src/github.com/cyokodog/claude-config/.claude/shared/cyk-browser-operations.md` の共通入口を目的 `browser`、クライアント `codex` で使い、Playwright MCPでそのURLを開く。ユーザーが操作できる可視のブラウザを使い、操作中のタブは閉じない。ヘッドレスしか使えない場合はその旨を伝える。
5. ユーザーに、ピッカーで調整して「この色に決定」を押し、チャットへ「決定した」と伝えるよう案内して待つ。AIが代わりに決定ボタンを押さない。初期色は決定値として扱わない。

起動や表示に失敗したら、原因を報告して止まる。ユーザーが色の直接指定へ切り替えると明示した場合だけ、ピッカーを使わずに手順4へ進む。

### 3. 決定値を検証する

ユーザーが決定を伝えたら、この回のセッションディレクトリの `choice.json` を読む。

- ファイルがなければ、まだ保存されていないことを伝えて色設定を書き込まない。
- `path` が手順1の対象パスと一致し、`session` が同じ `session.json` の値と一致することを確認する。別セッションの決定値は使わない。
- `hex` が `^[0-9a-f]{6}$` に一致することを検証する。明るさもその値から再計算する。
- 明るさが80を超える場合は警告し、明るい色でも適用する承認があるか確認する。未承認なら書き込まない。

検証できた値だけ手順4で反映する。決定後にピッカーを再調整した場合は、再度決定ボタンを押して保存した値を使う。適用完了または中止したら、自分が起動したサーバーの実行セッションを終了する。

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
