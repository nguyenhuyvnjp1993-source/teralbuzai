"""Đọc DXF 外形図 テラル, phân loại nét và làm phẳng thành polyline.

Hai kiểu file:
- kiểu mới (AC1015): loại nét nằm ở tên layer (T02--Continuous_25, T06--..., ...)
- kiểu cũ (AC1009): loại nét nằm ở layer viết hoa hoặc ở linetype của entity.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import ezdxf
import numpy as np
from ezdxf import path as ezpath

# loại nét
THAY = "thay"        # nét thấy (liền)
TAM = "tam"          # đường tâm (T06)
KHUAT = "khuat"      # nét khuất (T05)
TUONG = "tuong"      # nét tưởng tượng (T08), vd カップリングカバー
KHAC = "khac"


def loai_net(layer: str, linetype: str) -> str:
    s = (layer + "|" + linetype).upper()
    if s.startswith("T06") or "LONGDASHEDSHORTDASHED" in s or "CENTER" in s:
        return TAM
    if s.startswith("T08") or "DOUBLE-SHORT" in s or "PHANTOM" in s:
        return TUONG
    if s.startswith("T05") or "DASHED" in s or "HIDDEN" in s:
        return KHUAT
    if s.startswith("T02") or s.startswith("T01") or "CONTINUOUS" in s:
        return THAY
    return KHAC


@dataclass
class Net:
    """Một nét vẽ đã làm phẳng."""
    loai: str
    kieu: str               # LINE, ARC, CIRCLE...
    diem: np.ndarray        # (n,2)
    tam: tuple | None = None    # tâm (CIRCLE/ARC)
    ban_kinh: float | None = None

    @property
    def bbox(self):
        return (*self.diem.min(0), *self.diem.max(0))


@dataclass
class BanVe:
    ten_file: str
    phien_ban: str
    nets: list[Net] = field(default_factory=list)


def _linetype(e, doc) -> str:
    lt = e.dxf.get("linetype", "BYLAYER")
    if lt.upper() == "BYLAYER":
        try:
            lt = doc.layers.get(e.dxf.layer).dxf.linetype
        except Exception:
            lt = ""
    return lt


def _flatten(e, sai_so=0.2):
    try:
        p = ezpath.make_path(e)
    except Exception:
        return None
    pts = [(v.x, v.y) for v in p.flattening(sai_so)]
    if len(pts) < 2:
        return None
    return np.array(pts, dtype=float)


def doc_ban_ve(duong_dan: str) -> BanVe:
    doc = ezdxf.readfile(duong_dan)
    bv = BanVe(duong_dan, doc.dxfversion)
    msp = doc.modelspace()

    def them(e, doc):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "DIMENSION", "HATCH", "POINT", "ATTRIB", "ATTDEF"):
            return
        if t == "INSERT":
            for v in e.virtual_entities():
                them(v, doc)
            return
        lp = loai_net(e.dxf.layer, _linetype(e, doc))
        pts = _flatten(e)
        if pts is None:
            return
        tam = r = None
        if t in ("CIRCLE", "ARC"):
            tam = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
        bv.nets.append(Net(lp, t, pts, tam, r))

    for e in msp:
        them(e, doc)
    return bv
