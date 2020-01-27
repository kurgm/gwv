# gwv

[![Build Status](https://travis-ci.org/kurgm/gwv.svg?branch=master)](https://travis-ci.org/kurgm/gwv)
[![codecov](https://codecov.io/gh/kurgm/gwv/branch/master/graph/badge.svg)](https://codecov.io/gh/kurgm/gwv)

GlyphWiki data validator - https://kurgm.github.io/gwv-view/


## Installation

```sh
python setup.py install
```


## Usage

```sh
gwv /path/to/dump_newest_only.txt
```

（↑を実行すると `dump_newest_only.txt` と同じディレクトリに `gwv_result.json` が生成される（フォーマットは今後大きく変更する可能性がある））


## Test

```sh
python setup.py test
```


## License

MIT
