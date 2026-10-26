# Chrome 拡張（Manifest V3）

## YouTube などを自前の画面に iframe で埋め込むことはできない

- `youtube.com/watch` は `X-Frame-Options: SAMEORIGIN` を返す。埋め込めるのは `youtube.com/embed/<ID>` のプレイヤーだけ。
- 「見ているページに対して操作したい」なら、拡張のサイドパネルを使う。

## サイドパネルに localhost の画面を出すパターン

- `manifest.json`: `"permissions": ["sidePanel"]`、`"side_panel": {"default_path": "sidepanel.html"}`、`"background": {"service_worker": "background.js"}`。
- `background.js`: `chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })`。`action.default_popup` があるとポップアップが優先されるので消す。
- `sidepanel.html` に `<iframe src="http://localhost:<port>/">` を置き、今のタブの URL を `postMessage` で渡す。
  - 画面側は読み込み後に親へ `ready` を送り、親はそれを受けてから送る（読み込み順に依存しない）。
  - 親は送り先の origin を `http://localhost:<port>` に限定し、画面側は `event.origin` が `chrome-extension://` で始まるものだけ受け取る。
- タブの URL・タイトルは `tabs` 権限がなくても、`host_permissions` に入っているサイトなら `chrome.tabs.query` で取れる（対象外のサイトでは空になる）。
- YouTube はページ遷移しても再読み込みしないので、`chrome.tabs.onUpdated` の `changeInfo.url` も拾う。
- localhost のサーバーが落ちているかは、iframe からは分からない（エラーページが出るだけ）。親で `fetch` して確かめ、つながらなければ案内を出す（`host_permissions` に `http://localhost:<port>/*` を入れる）。
- iframe 内の `localStorage` は、普通のタブで開いたときとは別に保存される（ストレージの分割）。

## サイドパネルの localhost 画面から、拡張へ接続キーを自動で渡す

- 拡張自身が localhost のサーバーへ（WebSocket などで）つなぐ場合、サーバーの認証キーを手で設定させずに済ませられる。パネル内の画面（同一オリジンのセッションでキーを持っている）から親の拡張へ `postMessage` で渡す。
  - 画面側：`window.location.ancestorOrigins` が 1 件で `chrome-extension://[a-p]{32}` のときだけ、その origin を宛先にして送る。
  - 拡張側：`event.origin` が localhost のサーバーで、`event.source` が自分の iframe の `contentWindow` のときだけ受け取り、`chrome.storage.local` に保存する。
  - サーバー側：画面に `Content-Security-Policy: frame-ancestors 'self' chrome-extension:` を付け、他サイトに埋め込まれてキーを抜かれないようにする。
- 拡張自身がサーバーにつながず、iframe の画面だけがサーバーと話す構成なら、そもそもキーの受け渡しは要らない（YouTube ダウンローダーの構成）。

## content script とページの関係

- content script はページと同じ `sessionStorage` / `localStorage` を読み書きできる。サイトがタブの `sessionStorage` に残す入力途中の状態を消してから再読込すれば、空の画面から入れ直せる。
- SPA 内の画面遷移（`history.pushState`）では content script は動き続ける。`chrome.tabs.update` や再読込では作り直されるので、`chrome.tabs.sendMessage` で応答が返るまで ping してから依頼する。

## 拡張が使い回す専用タブ

- 「入力先のタブを毎回選ぶ」代わりに、初回に `chrome.tabs.create` で開いたタブの ID を `chrome.storage.session` に保存し、以降は `chrome.tabs.get` で生きていれば使い回す。閉じられていたら開き直す。`storage.session` はブラウザを再起動すると消える。

## 大きな画像をタブへ送る

- `chrome.tabs.sendMessage` で iPhone の写真（1 枚数 MB）を base64 で何枚も送ると、メッセージの上限に近づく。拡張ページ（サイドパネル）で `createImageBitmap(blob, { imageOrientation: 'from-image' })` → `OffscreenCanvas` → `convertToBlob({ type: 'image/jpeg' })` で縮小してから送る。EXIF の向きもここで反映される。
