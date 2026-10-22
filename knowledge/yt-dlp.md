# yt-dlp

## インストールが複数あると、更新したのに直らない

- Homebrew（`/opt/homebrew/bin/yt-dlp`）と pyenv / pip（`~/.pyenv/shims/yt-dlp`）の両方に入っていることがある。
- 対話シェルと、Raycast などから起動したプロセスでは PATH の順番が違い、別のほうが使われる。
- 確認: `which -a yt-dlp` と、実際に動いているプロセスの PATH。ログに `yt-dlp --version` を出しておくと切り分けが早い。
- 古いままだと YouTube の仕様変更に追いつけず、`HTTP Error 403: Forbidden` が出たり出なかったりする。まず全部を最新にする（`brew upgrade yt-dlp` と `pip install -U yt-dlp`）。

## `-o`（保存先）の `$VAR` は環境変数として展開される

- ファイル名に `$HOME` のような文字列が含まれると、パスに置き換わってフォルダが掘られる。
- `%` は出力テンプレートとして解釈されるので `%%` にエスケープする。
- 対策: パスに使う `$` は全角の `＄` などに置き換える（メタデータは元の文字のまま入れる）。

## シェルを通さず引数配列で起動する

- `exec("yt-dlp ... \"${title}\"")` のような文字列の組み立ては、`"` や `$`、バッククォートで壊れる。
- Node なら `spawn('yt-dlp', args)` / `execFile`。ffmpeg も同じ。

## 画質と形式

- `--extractor-args youtube:player_client=android` を付けると、PO Token がないため 360p（形式 18）しか取れなくなる。付けない。
- Music.app / QuickTime でそのまま再生したいなら H.264 + AAC を優先する（YouTube の H.264 は 1080p まで）:
  `-f "bv*[vcodec^=avc1][height<=1080]+ba[ext=m4a]/b[vcodec^=avc1][height<=1080]/bv*[height<=1080]+ba/b"`
- 確認: `yt-dlp -s --print "%(format_id)s %(resolution)s %(vcodec)s" -f "<式>" <URL>`

## 便利なオプション

- 最終的な保存先を知る: `--print-to-file after_move:filepath <ファイル>`（`--print` は `--quiet` を兼ねて進捗が消えるので使わない）。
- 進捗を機械的に読む: `--newline --progress-template "download:<任意の接頭辞> %(progress.downloaded_bytes)s %(progress.total_bytes)s %(progress.total_bytes_estimate)s"`。映像と音声を別々に落とすときは `[download] Destination:` の行で何本目かを数える。
- プレイリストの中身だけ取る: `--flat-playlist -J`（数秒）。Mix（`list=RD...`）は動画 ID が要るので、`playlist?list=` ではなく元の watch URL を渡す。
