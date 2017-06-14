#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import mmap
import os.path
import shutil
import tempfile
import urllib
import zipfile

import xlrd

logging.basicConfig()
log = logging.getLogger(__name__)

F2_ZIP_URL = "http://appsrv.cse.cuhk.edu.hk/~irg/irg/irg45/IRGN2088CJK_F2Attributes.zip"
EXTF_JSON_FILENAME = "extf.json"


def parseF2XLS(f2xls):
    result = {}

    bk = xlrd.open_workbook(file_contents=f2xls, on_demand=True)
    for sheet_num in [0, 1]:  # CJKF1v4.0, CJKF2v4.0
        sh = bk.sheet_by_index(sheet_num)
        rows = sh.get_rows()
        next(rows)  # skip header row
        for row in rows:
            # CJK_F Seq. No.
            assert row[0].ctype == xlrd.XL_CELL_TEXT
            seqno = row[0].value
            assert seqno.isdigit() and len(seqno) == 5

            sources = []
            for col_num in [8, 10, 12, 14]:
                # G, J, SAT, K Source Reference
                if row[col_num].ctype == xlrd.XL_CELL_EMPTY:
                    source = None
                else:
                    assert row[col_num].ctype == xlrd.XL_CELL_TEXT
                    source = row[col_num].value

                sources.append(source)

            result[seqno] = sources

    return result


def main():
    extfjson_path = os.path.join(os.path.dirname(__file__),
                                 "..", "gwv", "data", EXTF_JSON_FILENAME)
    extfjson_path = os.path.normpath(extfjson_path)

    if os.path.exists(extfjson_path):
        return

    log.info("Downloading {}...".format(F2_ZIP_URL))
    filename, headers = urllib.urlretrieve(F2_ZIP_URL)
    log.info("Download completed")

    with tempfile.TemporaryFile() as f2xlsfile:
        with zipfile.ZipFile(filename) as f2zip:
            with f2zip.open("IRGN2088CJK_F2Attributes.xls") as f2xls_zipextfile:
                shutil.copyfileobj(f2xls_zipextfile, f2xlsfile)

        f2xlsfile.seek(0)
        extfdat = parseF2XLS(
            mmap.mmap(f2xlsfile.fileno(), 0, access=mmap.ACCESS_READ))

    with open(extfjson_path, "w") as extfjson_file:
        json.dump(extfdat, extfjson_file, separators=(",", ":"))


if __name__ == '__main__':
    main()
