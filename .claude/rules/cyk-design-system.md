---
paths:
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.css"
  - "**/vite.config.*"
---

# 個人プロジェクトの UI は cyk-design-system を使う

個人プロジェクト（オーナーが `cyokodog`）で画面を作る・直すときは、自作の見た目を書く前に [cyk-design-system](https://github.com/cyokodog/cyk-design-system)（`~/src/github.com/cyokodog/cyk-design-system`、非公開）を使う。仕事のプロジェクトには適用しない。

- 構成は React + Vite を基本にする。参照は ghq の並びを前提に `file:` の相対パス（例: `"cyk-design-system": "file:../cyk-design-system"`）。
- **Vite に `resolve: { dedupe: ['react', 'react-dom'] }` を必ず書く。** `file:` はシンボリックリンクになり、デザインシステム側の React まで読まれてフックが壊れるため。
- 入口で `cyk-design-system/style.css`（必須）と `cyk-design-system/fonts.css`（任意）を読み、ルート要素に `cyk-root` クラスを付ける。
- 色・余白・文字サイズは `--cyk-*` の CSS 変数で書き、値を直書きしない。ライト・ダークは OS 設定に従う。
- 部品が足りないとき、他のプロジェクトでも使えそうならデザインシステム側に足す（その README の「部品を足すとき」に従う）。そのプロジェクト専用ならプロジェクト側に書く。
- 使い方の詳細はデザインシステムの `README.md` を読む。
