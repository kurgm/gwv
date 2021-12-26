#!/usr/bin/env python

import json
import logging
import os
from urllib.request import urlretrieve
from xml.etree.ElementTree import iterparse
import zipfile

logging.basicConfig()
log = logging.getLogger(__name__)

MJ_ZIP_URL = "https://moji.or.jp/wp-content/mojikiban/oscdl/mji.00502.zip"
MJ_JSON_FILENAME = "mj.json"


def kuten2gl(ku: int, ten: int):
    """句点コードをGL領域の番号に変換する"""
    return "{:02x}{:02x}".format(ku + 32, ten + 32)


def parseMjxml(mjxml):
    ns = "{urn:mojikiban:ipa:go:jp:mji}"
    mjdat = []
    mjit = iterparse(mjxml, events=("start", "end"))
    ev, root = next(mjit)
    for ev, elem in mjit:
        if ev != "end" or elem.tag != ns + "MJ文字情報":
            continue

        # [jmj,koseki,juki,nyukan,x0213,x0212,ucs,ivs,svs,toki,dkw,shincho,sdjt]
        # ucs, ivsは複数ある可能性あり
        mjrow = [None, None, None, None, None, None,
                 set(), set(), None, None, None, None, None]
        for ch in elem:
            if ch.tag == ns + "MJ文字図形名":
                mjrow[0] = ch.text[2:]  # strip "MJ"
            elif ch.tag == ns + "戸籍統一文字番号":
                if ch.text:
                    mjrow[1] = ch.text
            elif ch.tag == ns + "住基ネット統一文字コード":
                if ch.text:
                    mjrow[2] = ch.text[2:].lower()  # strip "J+"
            elif ch.tag == ns + "入管外字コード":
                if ch.text:
                    mjrow[3] = ch.text.lower()
            elif ch.tag == ns + "JISX0213":
                men, ku, ten = ch[0].text.split("-")
                mjrow[4] = men + "-" + kuten2gl(int(ku), int(ten))
            elif ch.tag == ns + "JISX0212":
                ku, ten = ch.text.split("-")
                mjrow[5] = kuten2gl(int(ku), int(ten))
            elif ch.tag == ns + "UCS":
                for gch in ch:
                    if gch.tag == ns + "対応するUCS":
                        if gch.text:
                            mjrow[6].add(gch.text[2:].lower())  # strip "U+"
                    elif gch.tag == ns + "対応する互換漢字":
                        mjrow[6].add(gch.text[2:].lower())  # strip "U+"
            elif ch.tag == ns + "IPAmj明朝フォント実装":
                for gch in ch:
                    if gch.tag == ns + "実装したUCS":
                        mjrow[6].add(gch.text[2:].lower())  # strip "U+"
                    elif gch.tag == ns + "実装したMoji_JohoIVS":
                        seq = gch.text.split("_")
                        mjrow[6].add(seq[0].lower())
                        # XXXX_E01YY -> uxxxx-ue01yy
                        mjrow[7].add("-".join("u" + cp.lower() for cp in seq))
                    elif gch.tag == ns + "実装したSVS":
                        seq = gch.text.split("_")
                        mjrow[6].add(seq[0].lower())
                        # XXXX_FE0Y -> uxxxx-ufe0y
                        mjrow[8] = "-".join("u" + cp.lower() for cp in seq)
            elif ch.tag == ns + "登記統一文字番号":
                mjrow[9] = ch.text
            elif ch.tag == ns + "大漢和":
                dkwnum = ch.text.lstrip("補").rstrip("#'")
                if ch.text.startswith("補"):
                    mjrow[10] = "h{:0>4}{}".format(
                        dkwnum, "d" * ch.text.count("'"))
                else:
                    mjrow[10] = "{:0>5}{}".format(
                        dkwnum, "d" * ch.text.count("'"))
            elif ch.tag == ns + "日本語漢字辞典":
                mjrow[11] = "{:0>5}".format(ch.text)
            elif ch.tag == ns + "新大字典":
                mjrow[12] = "{:0>5}".format(ch.text)

        # set to list
        mjrow[6] = list(mjrow[6])
        mjrow[7] = list(mjrow[7])

        mjdat.append(mjrow)

        # free memory
        root.clear()
    return mjdat


mjjson_path = os.path.join(
    os.path.dirname(__file__),
    "..", "gwv", "data", "3rd", MJ_JSON_FILENAME)
mjjson_path = os.path.normpath(mjjson_path)


def main(mjjson_path: str = mjjson_path):

    if os.path.exists(mjjson_path):
        return
    os.makedirs(os.path.dirname(mjjson_path), exist_ok=True)

    log.info("Downloading %s", MJ_ZIP_URL)
    filename, _headers = urlretrieve(MJ_ZIP_URL)
    log.info("Download completed")

    with zipfile.ZipFile(filename) as mjzip:
        with mjzip.open("mji.00502.xml") as mjxml:
            mjdat = parseMjxml(mjxml)

    with open(mjjson_path, "w") as mjjson_file:
        json.dump(mjdat, mjjson_file, separators=(",", ":"))


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
