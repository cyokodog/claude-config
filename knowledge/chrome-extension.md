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
