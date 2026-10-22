# Node / npm / Vite

## Node 20 付属の npm（10.8 系）で `Cannot read properties of null (reading 'edgesOut')`

- ピア依存の解決中に npm が落ちる不具合。Vite 8 系などを入れると出る。
- Node 22 系（npm 10.9 以降）にすると直る。Vite 8 は Node 20.19 / 22.12 以上が必要なので、新規の個人 PJ は `.node-version` を 22 系にする。
- nodenv の shims ではなく特定バージョンの bin が PATH に入っている環境では、`.node-version` を置いても切り替わらない。そのときは `PATH=~/.nodenv/versions/<版>/bin:$PATH` を前に付けて実行する。

## `file:` で参照したパッケージは React が二重になりうる

- `file:../pkg` はシンボリックリンクとして入り、Vite が実体のパスで解決するため、リンク先の `node_modules/react` まで読まれる。
- 使う側の Vite に `resolve: { dedupe: ['react', 'react-dom'] }` を書く。

## `github:owner/repo` で入れるパッケージ

- ビルド成果物ではなくソースが入る。`prepare` スクリプトでビルドさせれば、`dist/` をコミットしなくてよい。
- 非公開リポジトリは、git の認証がある環境（`gh auth login` 済み・SSH 鍵）でのみ入る。CI ではトークンが要る。

## TypeScript の CommonJS で `__dirname`

- `package.json` に `"type": "module"` がない TS（tsx / ts-node で実行）は CommonJS 扱いで `__dirname` が使える。ESM の Vite 設定では `import.meta.dirname` を使う。
