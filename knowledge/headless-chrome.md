# ヘッドレス Chrome

`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --screenshot=<png> --window-size=W,H <URL>`

- **ウィンドウ幅は最小 500px。** それより狭く指定しても 500px で描かれて右が切れる。狭い幅（サイドパネルなど）を確かめたいときは、幅を指定した `<iframe>` に入れたページを撮る。
- `--virtual-time-budget` は実際の通信（fetch）の完了を待たない。API の応答を待ちたいときは `--timeout=<ms>` にする。それでも安定しないことがあるので、見た目の確認はユーザーのブラウザで開いてもらうほうが早いこともある。
- SVG を透過 PNG に書き出す: `<img src=... width=N height=N>` だけのページを `--default-background-color=00000000 --force-device-scale-factor=1 --window-size=N,N` で撮り、`sips -c N N` で切り出す（rsvg-convert や ImageMagick がなくてもできる）。
