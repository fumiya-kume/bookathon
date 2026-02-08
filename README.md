## このリポジトリで「本を書く」場所と流れ

このリポジトリは **Re:VIEW（`.re`）** で原稿を書き、PDF/EPUB/HTML を生成する構成です。

- **原稿を書く場所**: `contents/` 配下の `*.re`
- **章の順番を決める場所**: `catalog.yml`
- **書名/著者/表紙/出力設定など**: `config.yml`
- **画像を置く場所**: `images/`

### まず何を編集すればいい？

- **まずは** `contents/sample.re` を開いて、本文を差し替えるのが最短です。
- **まえがき/あとがき**は `contents/00-preface.re` と `contents/99-postface.re` にあります。

### 章（ファイル）を追加する手順

1. `contents/` に `01-intro.re` のような新しい `.re` を作る（ファイル名は自由）
2. `catalog.yml` の `CHAPS:` にそのファイル名を追加する
   - **注意**: `catalog.yml` は **タブ文字禁止**（エラーになります）

### 画像の入れ方（例）

- 画像ファイルを `images/` に置く（例: `images/my-figure.png`）
- 原稿で `//image[my-figure][キャプション]` のように参照します
  - 例は `contents/sample.re` にあります（`DHP-Metaverse.png` の参照）

### ビルド（PDF/EPUB/HTML）

このプロジェクトには `Rakefile` があり、Re:VIEW コマンドを呼び出します。
ローカルに Ruby/Re:VIEW を入れずに試したい場合は **Docker** で完結できます。

```bash
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake pdf
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake epub
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake web
```

生成物:
- `book.pdf`
- `book.epub`
- `webroot/`（HTML一式）

### Re:VIEWの書式リファレンス

- `https://github.com/kmuto/review/blob/master/doc/format.ja.md`

### もう少し丁寧なガイド

- `WRITING_GUIDE.md` を参照してください（章の増やし方、運用のコツ、よくあるミスをまとめています）

---

## 補足（出典/派生テンプレについて）

この構成は Re:VIEW による執筆テンプレート（通称 ReBook 系）をベースにしています。
（関連リンクは履歴として残しています）

- `https://github.com/kaitas/ReBook/`



