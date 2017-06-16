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
import zipfile

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

import xlrd

logging.basicConfig()
log = logging.getLogger(__name__)

IRG2015_ZIP_URL = "http://appsrv.cse.cuhk.edu.hk/~irg/irg/irg47/IRGN2179CJK_Working_Set2015v3.0_Attributes.zip"
IRG2015_JSON_FILENAME = "irg2015.json"


def parseIRG2015XLS(irg2015xls):
    result = {}

    bk = xlrd.open_workbook(file_contents=irg2015xls, on_demand=True)
    sh = bk.sheet_by_index(0)  # IRGN2179IRG_Working_Set2015v3.0
    rows = sh.get_rows()
    next(rows)  # skip header row
    for row in rows:
        # Sequence Number
        assert row[0].ctype == xlrd.XL_CELL_TEXT
        seqno = row[0].value
        assert seqno.isdigit() and len(seqno) == 5

        sources = []
        for col_num in [2, 4, 6, 8, 10]:
            # UTC, T, K, SAT, G Source
            if row[col_num].ctype == xlrd.XL_CELL_EMPTY:
                source = None
            else:
                assert row[col_num].ctype == xlrd.XL_CELL_TEXT
                source = row[col_num].value

            sources.append(source)

        result[seqno] = sources

    return result


irg2015json_path = os.path.join(os.path.dirname(__file__),
                                "..", "gwv", "data", IRG2015_JSON_FILENAME)
irg2015json_path = os.path.normpath(irg2015json_path)


def main(irg2015json_path=irg2015json_path):

    if os.path.exists(irg2015json_path):
        return

    log.info("Downloading {}...".format(IRG2015_ZIP_URL))
    filename, headers = urlretrieve(IRG2015_ZIP_URL)
    log.info("Download completed")

    with tempfile.TemporaryFile() as irg2015xlsfile:
        with zipfile.ZipFile(filename) as irg2015zip:
            with irg2015zip.open("IRGN2179CJK_Working_Set2015v3.0_Attributes.xls") as irg2015xls_zipextfile:
                shutil.copyfileobj(irg2015xls_zipextfile, irg2015xlsfile)

        irg2015xlsfile.seek(0)
        irg2015dat = parseIRG2015XLS(
            mmap.mmap(irg2015xlsfile.fileno(), 0, access=mmap.ACCESS_READ))

    with open(irg2015json_path, "w") as irg2015json_file:
        json.dump(irg2015dat, irg2015json_file, separators=(",", ":"))


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
