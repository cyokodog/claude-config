# macOS のスクリプト

## AppleScript には値を argv で渡す

- スクリプトに `"${path}"` のように値を埋め込むと、`"` を含むパスやプレイリスト名で壊れる。
- `osascript -e 'on run argv' -e '... item 1 of argv ...' -e 'end run' <値1> <値2>` の形にして、値は引数で渡す。Node なら `execFile('osascript', [...lines.flatMap(l => ['-e', l]), ...args])`。
- 構文だけ確かめる: `osacompile -o /tmp/t.scpt -e ...`

## Music.app

- トラック番号がないと、アルバム内は曲名の ABC 順に並ぶ。プレイリストから取り込むときは曲順をトラック番号にする。
- 後から付け直す: `tell application "Music"` で `every file track whose artist is ... and album is ... and name is ...` を探し、`set track number of t to n` と `set track count of t to 総数`。
- ファイルを同じパスのまま上書きすれば、ライブラリの参照は切れない。

## 大量のファイルを書き換える前のバックアップ

- APFS では `cp -cR <元> <先>` でクローンが作れる。一瞬で終わり、空き容量もほぼ使わない。

## Raycast から起動したプロセス

- Raycast のスクリプトは対話シェルと PATH が違う（`~/raycast-scripts/my-apps.sh` は nodenv の shims と `/opt/homebrew/bin` を先頭に置く）。コマンドが別のバージョンで動いていないか疑う。
- `my-apps` で起動したプロセスは `~/.my-apps/run/<name>.pgid` のプロセスグループで管理されている。手で再起動するときも新しいプロセスグループで起動し、pgid を書き戻すと `my-apps-stop` で止められる（`set -m` が必要なので bash で実行する）。

## Finder で表示

- `open -R <パス>`
