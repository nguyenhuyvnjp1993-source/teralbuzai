"""So số đo mô hình với số ghi trên PDF 外形寸法図 (đọc bằng mắt, lưu ở data/sj_so_pdf.csv).

Tiêu chí 2: lệch không quá 1 mm.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

TOL = 1.0


def gia_tri_mo_hinh(bc: dict) -> dict:
    s = bc["so_do"]
    xs = [p[0] for p in s["base"]["da_giac"]]
    ys = [p[1] for p in s["base"]["da_giac"]]
    return {
        "base_dai": max(xs) - min(xs),
        "base_rong": max([max(ys) - min(ys)] +
                         [2 * max(abs(h["y0"]), abs(h["y1"])) for h in s["hop"] if h["ten"] == "ベース耳"]),
        "truc_z": s["truc_z"],
        "xa_z": s["xa"]["tam"][2],
        "hut_x": s["hut"]["tam"][0],
        "hut_D": s["hut"]["D_do"],
        "xa_D": s["xa"]["D_do"],
    }


def main(thu_muc: str, csv_pdf: str = "data/sj_so_pdf.csv"):
    hang = list(csv.DictReader(open(csv_pdf, encoding="utf-8")))
    loi = 0
    print("| mã | kích thước | PDF | mô hình | lệch | đạt |")
    print("|---|---|---:|---:|---:|---|")
    for h in hang:
        p = Path(thu_muc) / f"{h['ma']}.json"
        if not p.exists():
            continue
        mh = gia_tri_mo_hinh(json.loads(p.read_text(encoding="utf-8")))
        for k, v in mh.items():
            if not h.get(k):
                continue
            pdf = float(h[k])
            d = v - pdf
            ok = abs(d) <= TOL
            loi += not ok
            print(f"| {h['ma']} | {k} | {pdf:g} | {v:g} | {d:+.1f} | {'✓' if ok else '✗'} |")
    return loi


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:]) else 0)
