# 『ブラックホール応答理論』改訂試作版

著者：森川億人、小川翔也、廣瀬拓哉

## 内容

日本語モノグラフの改訂試作版です。学部四年生を想定し、古典場の因果的応答から共鳴のスペクトルを経て、量子線形応答、地平面の熱性、ETH、応答不変量までを一つの遅延 Green 関数で結びます。自己完結ではなく自己整合性を目標とし、既知の物理だけを本文の主線に置き、今後の研究は少数の「研究問題」へ移しています。

## 組版

upLaTeX、dvipdfmx、pbibtex、および索引生成用の mendex を用います。主ファイルは `main.tex` です。

```sh
uplatex main.tex
pbibtex main
mendex -U -d bhindex.dic main.idx
uplatex main.tex
uplatex main.tex
dvipdfmx main.dvi
```

通常は、プロジェクトのルートで次を実行してください。

```sh
make
```

`main.tex` では `imakeidx` を `noautomatic` オプション付きで読み込み、本文中の `\term{...}` から索引項目を `main.idx` に書き出します。`mendex` は `bhindex.dic` を使って日本語項目の読みを処理し、`main.ind` を生成します。索引は `\printindex` の位置に出力されます。

TeX Live の日本語環境、`jsbook`、`pxjahyper`、`tcolorbox`、`imakeidx`、`mendex` などが必要です。ローカルに同梱した `omphys.sty`、`natbib.sty`、`utphys.bst` を使用します。

## 構成

- `main.tex`：主ファイル
- `chapters/`：各章と付録
- `ref.bib`：参考文献データベース
- `bhindex.dic`：mendex 用の索引読み辞書
- `omphys.sty`：数式・物理記法
- `natbib.sty`、`utphys.bst`：参考文献組版
- `Makefile`：upLaTeX、pbibtex、mendex、dvipdfmx を順に実行するビルド設定

## 索引

索引に登録する専門用語は本文中で `\term{...}` として指定します。

```tex
\term{準固有振動}
```

`\term` は本文では `\textit{...}` として組版しつつ、同じ語を索引へ登録します。漢字を含む日本語項目の読みは `bhindex.dic` に記述します。

本改訂版では、「物理ミニマム」を編集原理とし、未来地平面の正則性、放射自由度、源から観測量への再構成、Kerr の最小限、ブラックホール熱力学を補いました。各章頭の引用は英語または英語原文と出典だけで組み、本文は参考文献を除いて百頁程度を編集上の目安とします。
