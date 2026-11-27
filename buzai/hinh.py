"""Hàm tìm nét theo hình dạng trong một hình chiếu."""
from __future__ import annotations

import numpy as np

from .dxf_doc import Net


def ngang(nets: list[Net], dai_min: float = 0.0, tol: float = 0.05):
    """Các đoạn thẳng nằm ngang: list (y, x0, x1, net)."""
    out = []
    for n in nets:
        if n.kieu != "LINE" and not (n.kieu in ("LWPOLYLINE", "POLYLINE") and len(n.diem) == 2):
            continue
        (xa, ya), (xb, yb) = n.diem[0], n.diem[-1]
        if abs(ya - yb) <= tol and abs(xb - xa) >= dai_min:
            out.append((ya, min(xa, xb), max(xa, xb), n))
    return out


def doc(nets: list[Net], dai_min: float = 0.0, tol: float = 0.05):
    """Các đoạn thẳng đứng: list (x, y0, y1, net)."""
    out = []
    for n in nets:
        if n.kieu != "LINE" and not (n.kieu in ("LWPOLYLINE", "POLYLINE") and len(n.diem) == 2):
            continue
        (xa, ya), (xb, yb) = n.diem[0], n.diem[-1]
        if abs(xa - xb) <= tol and abs(yb - ya) >= dai_min:
            out.append((xa, min(ya, yb), max(ya, yb), n))
    return out


def bbox(nets: list[Net]):
    a = np.array([n.bbox for n in nets])
    return a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max()


def trong_khoang_x(nets, x0, x1):
    """Nét có bbox giao [x0, x1] theo x."""
    return [n for n in nets if n.bbox[2] >= x0 and n.bbox[0] <= x1]


def trong_khoang_y(nets, y0, y1):
    return [n for n in nets if n.bbox[3] >= y0 and n.bbox[1] <= y1]
