"""Tách 3 hình chiếu (bằng, đứng, cạnh) của 外形図 bằng gom cụm theo khoảng cách."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dxf_doc import BanVe, Net, THAY


@dataclass
class Cum:
    nets: list[Net]

    @property
    def bbox(self):
        a = np.array([n.bbox for n in self.nets])
        return (a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max())

    @property
    def rong(self):
        b = self.bbox
        return b[2] - b[0]

    @property
    def cao(self):
        b = self.bbox
        return b[3] - b[1]

    def loc(self, *loai):
        return [n for n in self.nets if n.loai in loai]


def gom_cum(nets: list[Net], khe: float) -> list[list[int]]:
    """Gom các nét có bbox cách nhau <= khe vào một cụm (union-find)."""
    if not nets:
        return []
    a = np.array([n.bbox for n in nets])
    n = len(nets)
    cha = np.arange(n)

    def goc(i):
        while cha[i] != i:
            cha[i] = cha[cha[i]]
            i = cha[i]
        return i

    for i in range(n):
        x0, y0, x1, y1 = a[i]
        ov = (a[:, 0] <= x1 + khe) & (a[:, 2] >= x0 - khe) & (a[:, 1] <= y1 + khe) & (a[:, 3] >= y0 - khe)
        for j in np.nonzero(ov)[0]:
            p, q = goc(i), goc(int(j))
            if p != q:
                cha[p] = q
    nhom: dict[int, list[int]] = {}
    for i in range(n):
        nhom.setdefault(goc(i), []).append(i)
    return sorted(nhom.values(), key=len, reverse=True)


@dataclass
class BaHinhChieu:
    bang: Cum    # nhìn từ trên (平面)
    dung: Cum    # nhìn chính diện (正面), trục bơm nằm ngang
    canh: Cum    # nhìn từ phía hút (側面)


def tach_hinh_chieu(bv: BanVe, khe: float = 8.0) -> BaHinhChieu:
    """Tách 3 hình chiếu.

    Gom cụm bằng nét thấy, rồi gán nét tâm/khuất/tưởng tượng vào cụm có bbox chứa nó.
    Hình đứng và hình bằng thẳng cột với nhau (cùng khoảng x); hình cạnh nằm ngang hàng hình đứng.
    """
    thay = [n for n in bv.nets if n.loai == THAY]
    nhom = gom_cum(thay, khe)
    cums = [Cum([thay[i] for i in g]) for g in nhom if len(g) >= 20]
    # chỉ xét các cụm lớn
    cums = sorted(cums, key=lambda c: c.rong * c.cao, reverse=True)[:6]

    def chong_x(a, b):
        A, B = a.bbox, b.bbox
        ov = min(A[2], B[2]) - max(A[0], B[0])
        return ov / min(a.rong, b.rong)

    def chong_y(a, b):
        A, B = a.bbox, b.bbox
        ov = min(A[3], B[3]) - max(A[1], B[1])
        return ov / min(a.cao, b.cao)

    tot = None
    for i, d in enumerate(cums):
        for j, b in enumerate(cums):
            if i == j or chong_x(d, b) < 0.7 or b.bbox[1] < d.bbox[1]:
                continue
            for k, c in enumerate(cums):
                if k in (i, j) or chong_y(d, c) < 0.5 or c.bbox[0] < d.bbox[2] - 1:
                    continue
                diem = d.rong * d.cao + b.rong * b.cao + c.rong * c.cao
                if tot is None or diem > tot[0]:
                    tot = (diem, d, b, c)
    if tot is None:
        raise ValueError("không tách được 3 hình chiếu")
    _, dung, bang, canh = tot

    # gán nét không liền vào cụm chứa nó
    for n in bv.nets:
        if n.loai == THAY:
            continue
        x0, y0, x1, y1 = n.bbox
        for c in (dung, bang, canh):
            X0, Y0, X1, Y1 = c.bbox
            if x0 >= X0 - 30 and x1 <= X1 + 30 and y0 >= Y0 - 30 and y1 <= Y1 + 30:
                c.nets.append(n)
                break
    return BaHinhChieu(bang, dung, canh)
