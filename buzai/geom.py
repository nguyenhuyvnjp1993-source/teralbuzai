"""Khối cơ bản -> lưới tam giác (đỉnh, mặt). Đơn vị mm."""
from __future__ import annotations

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon


class Luoi:
    def __init__(self, v=None, f=None, ten=""):
        self.v = np.zeros((0, 3)) if v is None else np.asarray(v, float)
        self.f = np.zeros((0, 3), int) if f is None else np.asarray(f, int)
        self.ten = ten

    @property
    def so_tam_giac(self):
        return len(self.f)

    def bbox(self):
        return self.v.min(0), self.v.max(0)


def gop(luois: list[Luoi]) -> Luoi:
    vs, fs, n = [], [], 0
    for m in luois:
        vs.append(m.v)
        fs.append(m.f + n)
        n += len(m.v)
    return Luoi(np.vstack(vs), np.vstack(fs))


def hop(x0, x1, y0, y1, z0, z1, ten="") -> Luoi:
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], float)
    f = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
         [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
         [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
    return Luoi(v, f, ten)


def _doi(uvw, truc, goc):
    if truc == "x":
        p = np.stack([uvw[:, 2], uvw[:, 0], uvw[:, 1]], 1)
    elif truc == "y":
        p = np.stack([uvw[:, 1], uvw[:, 2], uvw[:, 0]], 1)
    else:
        p = uvw
    return p + np.asarray(goc, float)


def tru(r, w0, w1, truc="z", tam=(0.0, 0.0), n=24, ten="") -> Luoi:
    """Trụ tròn bán kính r, dọc trục `truc` từ w0 tới w1; `tam` là toạ độ (u, v) của trục.

    truc x: (u, v) = (y, z); truc y: (u, v) = (z, x); truc z: (u, v) = (x, y).
    """
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    u = tam[0] + r * np.cos(a)
    v = tam[1] + r * np.sin(a)
    duoi = np.stack([u, v, np.full(n, w0)], 1)
    tren = np.stack([u, v, np.full(n, w1)], 1)
    c0 = [[tam[0], tam[1], w0]]
    c1 = [[tam[0], tam[1], w1]]
    uvw = np.vstack([duoi, tren, c0, c1])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i]]
        f += [[2 * n, j, i], [2 * n + 1, n + i, n + j]]
    m = Luoi(_doi(uvw, truc, (0, 0, 0)), f, ten)
    return _dung_huong(m, w1 < w0)


def lang_tru(da_giac, w0, w1, truc="z", ten="") -> Luoi:
    """Đùn đa giác (u, v) theo trục `truc` từ w0 tới w1 (cùng quy ước (u, v) như `tru`)."""
    pg = Polygon(da_giac)
    if not pg.is_valid:
        pg = pg.buffer(0)
    if pg.exterior.is_ccw is False:
        pg = Polygon(list(pg.exterior.coords)[::-1])
    pts = np.array(pg.exterior.coords)[:-1]
    n = len(pts)
    tris = constrained_delaunay_triangles(pg)
    idx = {tuple(np.round(p, 6)): i for i, p in enumerate(pts)}
    f = []
    for t in tris.geoms:
        c = np.array(t.exterior.coords)[:3]
        ii = [idx.get(tuple(np.round(p, 6))) for p in c]
        if None in ii:
            continue
        # tam giác theo ccw trong (u, v)
        a, b, cc = pts[ii[0]], pts[ii[1]], pts[ii[2]]
        if (b[0] - a[0]) * (cc[1] - a[1]) - (b[1] - a[1]) * (cc[0] - a[0]) < 0:
            ii = [ii[0], ii[2], ii[1]]
        f.append([ii[0], ii[2], ii[1]])          # đáy (hướng -w)
        f.append([n + ii[0], n + ii[1], n + ii[2]])  # nắp (hướng +w)
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i]]
    uvw = np.vstack([np.c_[pts, np.full(n, w0)], np.c_[pts, np.full(n, w1)]])
    m = Luoi(_doi(uvw, truc, (0, 0, 0)), f, ten)
    return _dung_huong(m, w1 < w0)


def _dung_huong(m: Luoi, dao: bool) -> Luoi:
    """Bảo đảm pháp tuyến hướng ra ngoài (thể tích dương)."""
    v, f = m.v, m.f
    vol = np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum()
    if vol < 0:
        m.f = f[:, [0, 2, 1]]
    return m
