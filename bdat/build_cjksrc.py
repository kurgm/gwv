#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os.path
import shutil
import tempfile
import urllib
import zipfile

logging.basicConfig()
log = logging.getLogger(__name__)

UCS_ZIP_URL = "http://standards.iso.org/ittf/PubliclyAvailableStandards/c066791_IEC_10646_2014_Amd_2_2016_Electronic_inserts.zip"
CJKSRC_JSON_FILENAME = "cjksrc.json"


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


def main():
    cjksrcjson_path = os.path.join(os.path.dirname(__file__),
                                   "..", "gwv", "data", CJKSRC_JSON_FILENAME)
    cjksrcjson_path = os.path.normpath(cjksrcjson_path)

    if os.path.exists(cjksrcjson_path):
        return

    log.info("Downloading {}...".format(UCS_ZIP_URL))
    opener = urllib.FancyURLopener()
    opener.addheader(
        "Cookie", "url_ok=/ittf/PubliclyAvailableStandards/c066791_IEC_10646_2014_Amd_2_2016_Electronic_inserts.zip")
    filename, headers = opener.retrieve(UCS_ZIP_URL)
    log.info("Download completed")

    with tempfile.TemporaryFile() as ucszipfile_seekable:
        with zipfile.ZipFile(filename) as isozip:
            with isozip.open("C066791e_Electronic_inserts.zip") as ucszipfile:
                shutil.copyfileobj(ucszipfile, ucszipfile_seekable)

        with zipfile.ZipFile(ucszipfile_seekable) as ucszip:
            with ucszip.open("CJKSrc.txt") as cjksrctxt:
                cjksrc = parseCJKSrc(cjksrctxt)

    with open(cjksrcjson_path, "w") as cjksrcjson_file:
        json.dump(cjksrc, cjksrcjson_file, separators=(",", ":"))


if __name__ == '__main__':
    main()
