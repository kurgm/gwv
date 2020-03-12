#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import json
import logging
import os.path
import zipfile

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

logging.basicConfig()
log = logging.getLogger(__name__)

CJKSRC_URL = "https://www.unicode.org/wg2/iso10646/edition5/data/CJKSrc.txt"
UNIHAN_ZIP_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"
CJKSRC_JSON_FILENAME = "cjksrc.json"


def get_iso_CJKSrc(url=CJKSRC_URL):
    log.info("Downloading {}...".format(url))
    filename, _headers = urlretrieve(url)
    log.info("Download completed")

    with open(filename) as cjksrctxt:
        return parseCJKSrc(cjksrctxt)


def get_unihan_CJKSrc(url=UNIHAN_ZIP_URL):
    log.info("Downloading {}...".format(url))
    filename, _headers = urlretrieve(url)
    log.info("Download completed")

    with zipfile.ZipFile(filename) as unihanzip:
        with unihanzip.open("Unihan_IRGSources.txt") as cjksrctxt:
            return parseCJKSrc(codecs.iterdecode(cjksrctxt, "utf-8"))


def parseCJKSrc(cjksrctxt):
    result = {}
    tag2idx = dict(zip([
        "kIRG_GSource",
        "kIRG_TSource",
        "kIRG_JSource",
        "kIRG_KSource",
        "kIRG_KPSource",
        "kIRG_VSource",
        "kIRG_HSource",
        "kIRG_MSource",
        "kIRG_USource",
        "kIRG_SSource",
        "kIRG_UKSource",
        "kCompatibilityVariant"
    ], range(10)))

    for line in cjksrctxt:
        if not line.startswith("U+"):
            continue
        ucs, tag, val = line.rstrip().split("\t")
        if tag not in tag2idx:
            continue
        ucs = "u" + ucs[2:].lower()
        if ucs not in result:
            result[ucs] = [None] * 10
        result[ucs][tag2idx[tag]] = val

    return result


cjksrcjson_path = os.path.join(os.path.dirname(__file__),
                               "..", "gwv", "data", CJKSRC_JSON_FILENAME)
cjksrcjson_path = os.path.normpath(cjksrcjson_path)


def main(cjksrcjson_path=cjksrcjson_path):

    if os.path.exists(cjksrcjson_path):
        return

    cjksrc = get_unihan_CJKSrc()

    with open(cjksrcjson_path, "w") as cjksrcjson_file:
        json.dump(cjksrc, cjksrcjson_file, separators=(",", ":"))


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
