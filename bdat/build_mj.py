#!/usr/bin/env python

from collections import defaultdict
import json
import logging
import os
from urllib.request import urlretrieve
from typing import Any, Dict, IO, List

from .strict_xlsx import iterxlsx

logging.basicConfig()
log = logging.getLogger(__name__)

MJ_XLSX_URL = "https://moji.or.jp/wp-content/uploads/2024/01/mji.00602.xlsx"
MJ_JSON_FILENAME = "mj.json"


def kuten2gl(ku: int, ten: int):
    """句点コードをGL領域の番号に変換する"""
    return "{:02x}{:02x}".format(ku + 32, ten + 32)


def parseMjxlsx(mjxlsx: IO[bytes]):
    mjdat: List[List] = []
    mjit = iterxlsx(mjxlsx, "sheet1")
    header = next(mjit)
    for row in mjit:
        rowdata: Dict[str, Any] = defaultdict(lambda: None, {
            header[col]: value
            for col, value in row.items()
        })
        # [jmj,koseki,juki,nyukan,x0213,x0212,ucs,ivs,svs,toki,dkw,shincho,sdjt]
        # ucs, ivsは複数ある可能性あり
        mjrow = [None, None, None, None, None, None,
                 set(), set(), None, None, None, None, None]
        mjrow[0] = rowdata["MJ文字図形名"][2:]  # strip "MJ"
        chtext = rowdata["戸籍統一文字番号"]
        if chtext:
            mjrow[1] = chtext
        chtext = rowdata["住基ネット統一文字コード"]
        if chtext:
            mjrow[2] = chtext[2:].lower()  # strip "J+"
        chtext = rowdata["入管外字コード"]
        if chtext:
            mjrow[3] = chtext[2:].lower()  # strip "0x"
        chtext = rowdata["X0213"]
        if chtext:
            men, ku, ten = chtext.split("-")
            mjrow[4] = men + "-" + kuten2gl(int(ku), int(ten))
        chtext = rowdata["X0212"]
        if chtext:
            ku, ten = chtext.split("-")
            mjrow[5] = kuten2gl(int(ku), int(ten))
        chtext = rowdata["対応するUCS"]
        if chtext:
            mjrow[6].add(chtext[2:].lower())  # strip "U+"
        chtext = rowdata["対応する互換漢字"]
        if chtext:
            mjrow[6].add(chtext[2:].lower())  # strip "U+"
        chtext = rowdata["実装したUCS"]
        if chtext:
            mjrow[6].add(chtext[2:].lower())  # strip "U+"
        chtext = rowdata["実装したMoji_JohoコレクションIVS"]
        if chtext:
            for ivs in chtext.split(";"):
                seq = ivs.split("_")
                mjrow[6].add(seq[0].lower())
                # XXXX_E01YY -> uxxxx-ue01yy
                mjrow[7].add("-".join("u" + cp.lower() for cp in seq))
        chtext = rowdata["実装したSVS"]
        if chtext:
            seq = chtext.split("_")
            mjrow[6].add(seq[0].lower())
            # XXXX_FE0Y -> uxxxx-ufe0y
            mjrow[8] = "-".join("u" + cp.lower() for cp in seq)
        chtext = rowdata["登記統一文字番号(参考)"]
        if chtext:
            mjrow[9] = chtext
        chtext = rowdata["大漢和"]
        if chtext:
            chtext = str(chtext)
            dkwnum = chtext.lstrip("補").rstrip("#'")
            if chtext.startswith("補"):
                mjrow[10] = "h{:0>4}{}".format(
                    dkwnum, "d" * chtext.count("'"))
            else:
                mjrow[10] = "{:0>5}{}".format(
                    dkwnum, "d" * chtext.count("'"))
        chtext = rowdata["日本語漢字辞典"]
        if chtext:
            mjrow[11] = "{:0>5}".format(chtext)
        chtext = rowdata["新大字典"]
        if chtext:
            mjrow[12] = "{:0>5}".format(chtext)

        # set to list
        mjrow[6] = list(mjrow[6])
        mjrow[7] = list(mjrow[7])

        mjdat.append(mjrow)
    return mjdat


mjjson_path = os.path.join(
    os.path.dirname(__file__),
    "..", "gwv", "data", "3rd", MJ_JSON_FILENAME)
mjjson_path = os.path.normpath(mjjson_path)


def main(mjjson_path: str = mjjson_path):

    if os.path.exists(mjjson_path):
        return
    os.makedirs(os.path.dirname(mjjson_path), exist_ok=True)

    log.info("Downloading %s", MJ_XLSX_URL)
    filename, _headers = urlretrieve(MJ_XLSX_URL)
    log.info("Download completed")

    with open(filename, "rb") as mjxlsx:
        mjdat = parseMjxlsx(mjxlsx)

    with open(mjjson_path, "w") as mjjson_file:
        json.dump(mjdat, mjjson_file, separators=(",", ":"))


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
