# gwv

[![Test](https://github.com/kurgm/gwv/actions/workflows/test.yml/badge.svg)](https://github.com/kurgm/gwv/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kurgm/gwv/branch/master/graph/badge.svg)](https://codecov.io/gh/kurgm/gwv)

GlyphWiki data validator

[グリフウィキ](https://glyphwiki.org/)に登録されているグリフデータから“気になるグリフ”を抽出するプログラムです。

抽出されたグリフを一覧できるページ: https://kurgm.github.io/gwv-view/

（関連: ↑の一覧ページのソース: <https://github.com/kurgm/gwv-view>）

## Installation

```sh
pip install git+https://github.com/kurgm/gwv.git@master#egg=gwv
```


## Usage

```sh
# Download the target dataset from GlyphWiki
curl https://glyphwiki.org/dump.tar.gz | tar -xzf - dump_newest_only.txt

# Run the program
gwv /path/to/dump_newest_only.txt
```

（↑を実行すると `dump_newest_only.txt` と同じディレクトリに `gwv_result.json` が生成される（フォーマットは今後大きく変更する可能性がある））

### Options

```
  -h, --help            show this help message and exit
  -o OUT, --out OUT     File to write the output JSON to
  -n [NAMES ...], --names [NAMES ...]
                        Names of validators
  -v, --version         show program's version number and exit
```

## License

MIT
