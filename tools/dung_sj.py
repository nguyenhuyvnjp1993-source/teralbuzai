"""Dựng 部材 dòng SJ từ DXF 外形図 và ghi IFC cho Rebro.

Ví dụ:
    python tools/dung_sj.py --dxf PC4-13978-0.dxf --ma SJ32X32L5.75-e --ra out/
    python tools/dung_sj.py --zip "テラル-陸上ポンプ-0527_SJ32X32L5.75-e.zip" --ra out/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from buzai.geom import gop  # noqa: E402
from buzai.ifc_rebro import ThongTinBuzai, ghi_ifc  # noqa: E402
from buzai.mo_hinh_sj import dau_noi_sj, dung_sj  # noqa: E402
from buzai.sj import do_sj  # noqa: E402

TRAN_TAM_GIAC = 5000


def dxf_tu_zip(zp: Path, thu_muc: Path) -> Path:
    with zipfile.ZipFile(zp) as z:
        ten = [n for n in z.namelist() if n.lower().endswith(".dxf")]
        if len(ten) != 1:
            raise SystemExit(f"{zp.name}: cần đúng 1 DXF, thấy {len(ten)}")
        return Path(z.extract(ten[0], thu_muc))


def ma_tu_ten_zip(ten: str) -> str:
    m = re.match(r".*?_(.+)\.zip$", ten)
    return m.group(1) if m else Path(ten).stem


def dung(dxf: Path, ma: str, ra: Path, kieu_hinh: str = "tess") -> dict:
    s = do_sj(str(dxf), ma)
    luois = dung_sj(s)
    so_tg = sum(m.so_tam_giac for m in luois)
    if so_tg > TRAN_TAM_GIAC:
        raise SystemExit(f"{ma}: {so_tg} tam giác > trần {TRAN_TAM_GIAC}")
    tt = ThongTinBuzai(ten_kieu="SJ型渦巻ポンプ" if not ma.upper().startswith("SJ4") else
                       ("SJ4S型渦巻ポンプ" if ma.upper().startswith("SJ4S") else "SJ4型渦巻ポンプ"),
                       ma_hang=ma, dau_noi=dau_noi_sj(s))
    ra.mkdir(parents=True, exist_ok=True)
    ghi_ifc(str(ra / f"{ma}.ifc"), tt, luois, kieu_hinh)
    tong = gop(luois)
    lo, hi = tong.bbox()
    bc = {
        "ma": ma, "ban_ve": s.ban_ve, "so_tam_giac": so_tg,
        "bao": {"x": [round(float(lo[0]), 1), round(float(hi[0]), 1)], "y": [round(float(lo[1]), 1), round(float(hi[1]), 1)],
                "z": [round(float(lo[2]), 1), round(float(hi[2]), 1)]},
        "dau_noi": [d.chuoi() for d in tt.dau_noi],
        "so_do": s.to_dict(),
    }
    (ra / f"{ma}.json").write_text(json.dumps(bc, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return bc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--ma")
    ap.add_argument("--zip", nargs="*")
    ap.add_argument("--ra", default="out")
    ap.add_argument("--hinh", choices=["tess", "brep"], default="tess")
    a = ap.parse_args()
    ra = Path(a.ra)
    if a.dxf:
        bc = dung(Path(a.dxf), a.ma or Path(a.dxf).stem, ra, a.hinh)
        print(bc["ma"], bc["so_tam_giac"], bc["bao"])
    for z in a.zip or []:
        zp = Path(z)
        with tempfile.TemporaryDirectory() as td:
            bc = dung(dxf_tu_zip(zp, Path(td)), ma_tu_ten_zip(zp.name), ra, a.hinh)
        print(bc["ma"], bc["so_tam_giac"], bc["bao"])


if __name__ == "__main__":
    main()
