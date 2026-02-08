## 執筆ガイド（このリポジトリで本を書くとき）

このリポジトリは **Re:VIEW（`.re`）** で原稿を書き、`rake` で **PDF/EPUB/HTML** を生成します。
「どこに何を書くか」だけに絞って、迷いやすい点を先に整理します。

---

## どこに何を書く？

- **本文・章の原稿**: `contents/*.re`
  - 例: `contents/sample.re`
- **まえがき**: `contents/00-preface.re`（`catalog.yml` の `PREDEF`）
- **あとがき**: `contents/99-postface.re`（`catalog.yml` の `POSTDEF`）
- **章の並び順（本の目次）**: `catalog.yml`
- **書名/著者/表紙/出力設定**: `config.yml`
- **画像**: `images/`
- **スタイル（EPUB/HTML）**: `style.css`
- **PDF向けのLaTeXスタイル**: `sty/`

---

## 新しい章を追加する（最短手順）

### 1) `contents/` に `.re` を作る

ファイル名は自由ですが、並びが分かりやすいので `NN-...` を推奨します。

- 例: `contents/01-intro.re`

`01-intro.re` の最小例:

```text
= はじめに

== この章で扱うこと

本文を書きます。
```

### 2) `catalog.yml` の `CHAPS:` に追記する

例（`sample.re` の代わりに `01-intro.re` を入れる）:

```yaml
CHAPS:
  - 01-intro.re
```

**注意（重要）**:
- `catalog.yml` は **タブ文字禁止**（スペースでインデントしてください）
- `config.yml` で `contentdir: contents` になっているので、`catalog.yml` には **`contents/` を付けず**ファイル名だけを書きます

---

## 画像を入れる

1. `images/` に画像を置く（例: `images/my-figure.png`）
2. `.re` から参照する

例（キャプション付き）:

```text
//image[my-figure][キャプション]
```

ポイント:
- `[]` の中の識別子は、基本的に **拡張子を除いたファイル名**を使うのが分かりやすいです（例: `my-figure`）
- 迷ったら `contents/sample.re` の例に合わせるのが安全です

---

## 章リンク（別の章を参照する）

`contents/00-preface.re` にある例のように、章の参照は `@<chap>{...}` を使えます。

```text
@<chap>{sample}
```

ここで指定するのは、通常 **`.re` の拡張子を除いたファイル名**です（例: `sample.re` → `sample`）。

---

## コード・脚注（よく使うものだけ）

### コード（例）

`contents/sample.re` に例があります。

```text
//list[id][キャプション][c]{
int main() { return 0; }
//}
```

### 脚注（例）

```text
本文中に脚注を入れます@<fn>{note1}。

//footnote[note1][脚注本文]
```

---

## ビルド（Dockerで完結）

ローカルに Ruby/Re:VIEW/TeX を入れずに生成するなら、以下が一番簡単です。

```bash
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake pdf
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake epub
docker run --rm -v "$PWD:/work" -w /work vvakame/review:5.5 rake web
```

出力:
- `book.pdf`
- `book.epub`
- `webroot/`

---

## 迷ったとき（書式リファレンス）

- Re:VIEW フォーマット: `https://github.com/kmuto/review/blob/master/doc/format.ja.md`

