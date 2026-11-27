"""Đo 外形図 dòng SJ (渦巻ポンプ, trục ngang, hút đầu trục, xả thẳng đứng lên).

Hệ toạ độ mô hình (mm):
- X dọc trục bơm, từ モータ sang ポンプ (hướng dòng hút đi vào là -X).
- Y nằm ngang vuông góc trục, dương về phía sau hình đứng (phía trên của hình bằng).
- Z thẳng đứng, Z = 0 ở đáy ベース.
- Gốc X, Y đặt tại tâm 吐出フランジ (chiếu xuống đáy ベース).
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict

import numpy as np

from .chuan import flange_gan_nhat
from .dxf_doc import BanVe, doc_ban_ve
from .hinh import bbox, doc, ngang
from .raster import lam_bong
from .views import tach_hinh_chieu, Cum


@dataclass
class Flange:
    co: int              # 呼び径 A
    D: float             # đường kính ngoài
    t: float             # chiều dày
    tam: tuple           # (x, y, z) tâm mặt bích (mặt ngoài)
    huong: tuple         # vector pháp tuyến hướng ra ngoài
    D_do: float          # đường kính đo trên DXF
    ghi_chu: str = ""


@dataclass
class DoanTru:
    """Đoạn trụ đồng trục bơm (X) hoặc hộp nếu tiết diện không tròn."""
    x0: float
    x1: float
    r: float
    ten: str


@dataclass
class Hop:
    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float
    ten: str
    uoc_luong: bool = False


@dataclass
class LangTru:
    """Lăng trụ: đa giác trong mặt phẳng (Y, Z), đùn theo X từ x0 đến x1."""
    x0: float
    x1: float
    da_giac: list          # [(y, z), ...]
    ten: str


@dataclass
class DayBase:
    """Đa giác ベース trong mặt bằng (X, Y), đùn theo Z từ 0 đến cao."""
    da_giac: list
    cao: float


@dataclass
class SoDoSJ:
    ma: str
    ban_ve: str
    truc_z: float
    dai_tong: float
    cao_tong: float
    base: DayBase
    hut: Flange
    xa: Flange
    motor: list = field(default_factory=list)       # DoanTru
    hop: list = field(default_factory=list)         # Hop
    ong_truc: list = field(default_factory=list)    # DoanTru phía bơm (ブラケット, 軸)
    vo: LangTru | None = None                       # ケーシング
    ong_xa: DoanTru | None = None                   # 吐出ノズル (x0,x1 = z dưới, z trên)
    R_vo: float = 0.0
    goc_hinh: dict = field(default_factory=dict)    # gốc mô hình trên từng hình chiếu DXF
    ghi_chu: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def co_tu_ma(ma: str):
    """SJ4-150X125J530-e -> (150, 125) = (hút, xả)."""
    m = re.search(r"(\d+)X(\d+)", ma.upper())
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def _nhom_tron_dong_tam(cum: Cum, d_min=40.0):
    nhom = defaultdict(list)
    for n in cum.nets:
        if n.kieu == "CIRCLE" and 2 * n.ban_kinh >= d_min:
            nhom[(round(n.tam[0], 0), round(n.tam[1], 0))].append(n)
    return sorted(nhom.values(), key=lambda g: (-len(g), -max(2 * n.ban_kinh for n in g)))


def _profile(b, xs, tam, chieu):
    """Khoảng cách từ tâm tới biên bóng theo chiều (+1 lên, -1 xuống) tại các cột xs."""
    out = []
    for x in xs:
        c = b.tam_y(x)
        if c is None:
            out.append(0.0)
            continue
        col = b.cot(x)
        idx = np.nonzero(col)[0]
        ys = b.y0 + idx * b.buoc
        if chieu > 0:
            ys = ys[ys >= tam]
            out.append(ys.max() - tam if len(ys) else 0.0)
        else:
            ys = ys[ys <= tam]
            out.append(tam - ys.min() if len(ys) else 0.0)
    return np.array(out)


def _chia_bac(xs, r, sai=4.0, dai_min=15.0):
    """Chia profile r(x) thành các bậc gần hằng số: list [x0, x1, r]."""
    bac = []
    i0 = 0
    for i in range(1, len(xs) + 1):
        if i == len(xs) or abs(r[i] - np.median(r[i0:i])) > sai:
            bac.append([xs[i0], xs[i - 1], float(np.median(r[i0:i])), i - i0])
            i0 = i
    # gộp bậc ngắn vào bậc kề dài hơn (giữ bán kính của bậc dài)
    while len(bac) > 1:
        k = min(range(len(bac)), key=lambda i: bac[i][1] - bac[i][0])
        if bac[k][1] - bac[k][0] >= dai_min:
            break
        if k == 0:
            j = 1
        elif k == len(bac) - 1:
            j = k - 1
        else:
            j = k - 1 if bac[k - 1][1] - bac[k - 1][0] >= bac[k + 1][1] - bac[k + 1][0] else k + 1
        a_, b_ = sorted((k, j))
        bac[a_:b_ + 1] = [[bac[a_][0], bac[b_][1], bac[j][2], bac[a_][3] + bac[b_][3]]]
    # gộp bậc kề có bán kính gần nhau
    gon = []
    for b in bac:
        if gon and abs(b[2] - gon[-1][2]) <= sai:
            p = gon[-1]
            p[2] = (p[2] * p[3] + b[2] * b[3]) / (p[3] + b[3])
            p[1], p[3] = b[1], p[3] + b[3]
        else:
            gon.append(list(b))
    return [(a, b, r) for a, b, r, _ in gon]


def do_sj(duong_dan_dxf: str, ma: str) -> SoDoSJ:
    bv: BanVe = doc_ban_ve(duong_dan_dxf)
    h = tach_hinh_chieu(bv)
    D, B, C = h.dung, h.bang, h.canh
    ghi = []
    co_hut, co_xa = co_tu_ma(ma)

    # ---- hình cạnh: trục, mặt bích hút
    thC = C.loc("thay")
    _, cz0, _, _ = bbox(thC)
    g = _nhom_tron_dong_tam(C)[0]
    cy_side, cz_side = g[0].tam
    truc_z = cz_side - cz0
    D_hut_do = max(2 * n.ban_kinh for n in g)

    # ---- hình đứng
    thD = D.loc("thay")
    dx0, dz0, dx1, dz1 = bbox(thD)
    zc_D = dz0 + truc_z           # trục trên hình đứng

    # ---- hình bằng: tâm trục theo Y = tâm nhóm tròn mặt bích xả
    thB = B.loc("thay")
    bx0, by0, bx1, by1 = bbox(thB)
    gB = _nhom_tron_dong_tam(B)
    # nhóm tròn của mặt bích xả nằm gần đầu bơm (x lớn)
    gB = sorted(gB, key=lambda g: (-len(g) >= -2, -g[0].tam[0]))
    gxa = max([g for g in gB if len(g) >= 2], key=lambda g: g[0].tam[0])
    xd_B, yd_B = gxa[0].tam
    D_xa_do = max(2 * n.ban_kinh for n in gxa)
    # trục bơm trên hình bằng: nhóm tròn xả nằm trên trục (bơm SJ xả thẳng trên tâm)
    yc_B = yd_B
    # đổi toạ độ x hình bằng sang hình đứng (thẳng cột, nhưng có thể lệch nhỏ)
    lechx = 0.0
    # gốc: tâm xả
    X0 = xd_B + lechx

    def X(x):
        return x - X0

    # ---- mặt bích xả trên hình đứng
    co, tt, lech = flange_gan_nhat(D_xa_do, co_xa)
    R = tt[0] / 2
    gan = [n for n in thD if n.bbox[2] >= xd_B - R - 1 and n.bbox[0] <= xd_B + R + 1]
    ztop = max(n.bbox[3] for n in gan)
    hz = sorted({round(y, 2) for y, a, b, n in ngang(gan, dai_min=0.8 * tt[0])}, reverse=True)
    hz2 = [v for v in hz[1:] if 8 <= hz[0] - v <= 45]
    t_xa = hz[0] - hz2[0] if hz2 else tt[2]
    xa = Flange(co, tt[0], round(t_xa, 1), (0.0, 0.0, round(ztop - dz0, 1)), (0, 0, 1), round(D_xa_do, 1),
                "ép JIS10K" if abs(lech) > 0.5 else "")
    if co_xa and co != co_xa:
        ghi.append(f"cỡ xả đo {co}A khác mã {co_xa}A")

    # ---- mặt bích hút trên hình đứng
    co_h, th_, lech_h = flange_gan_nhat(D_hut_do, co_hut)
    vs = sorted({round(x, 2) for x, a, b, n in doc(thD, dai_min=0.8 * th_[0])}, reverse=True)
    xs_face = dx1
    vs2 = [v for v in vs[1:] if 8 <= vs[0] - v <= 45]
    t_hut = vs[0] - vs2[0] if vs2 else th_[2]
    hut = Flange(co_h, th_[0], round(t_hut, 1), (round(X(xs_face), 1), 0.0, round(truc_z, 1)), (1, 0, 0),
                 round(D_hut_do, 1), "ép JIS10K" if abs(lech_h) > 0.5 else "")
    if co_hut and co_h != co_hut:
        ghi.append(f"cỡ hút đo {co_h}A khác mã {co_hut}A")

    # ---- ベース: chiều dài từ đường đáy hình đứng
    day = max([t for t in ngang(thD) if abs(t[0] - dz0) < 0.5], key=lambda t: t[2] - t[1])
    base_x0, base_x1 = day[1], day[2]
    # chiều cao ベース (hình đứng): ベース kênh thép có đường ngang chạy suốt chiều dài;
    # ベース đúc thì lấy đường ngang cao nhất dài >= 15% chiều dài, thấp hơn 0.45 chiều cao trục.
    Lb = base_x1 - base_x0
    ngD = [t for t in ngang(thD, dai_min=0.15 * Lb) if 3 < t[0] - dz0 < 0.45 * truc_z]
    suot = [t for t in ngD if t[2] - t[1] >= 0.9 * Lb]
    tren = max(suot or ngD, key=lambda t: t[0]) if (suot or ngD) else None
    base_cao = (tren[0] - dz0) if tren else 0.12 * truc_z
    if not tren:
        ghi.append("không thấy mặt trên ベース, lấy 0.12 chiều cao trục")
    # bề rộng ベース theo X: dùng bóng hình bằng, phân vị thấp để bỏ tai bu lông, hộp đấu dây
    bongB = lam_bong(thB, buoc=0.5)
    xs = np.arange(base_x0 + 3, base_x1 - 3, 1.0)
    up = _profile(bongB, xs, yc_B, +1) - 0.5     # trừ nửa bề dày nét raster
    dn = _profile(bongB, xs, yc_B, -1) - 0.5
    nua = np.minimum(up, dn)
    # đa giác ベース: chia bậc bề rộng (tai bu lông ngắn bị gộp vào bậc kề)
    bacs = _chia_bac(xs, nua, sai=6.0, dai_min=40.0)
    poly_top = []
    for x0_, x1_, r_ in bacs:
        poly_top += [(X(x0_), r_), (X(x1_) + 1.0, r_)]
    poly_top[0] = (X(base_x0), poly_top[0][1])
    poly_top[-1] = (X(base_x1), poly_top[-1][1])
    da_giac = poly_top + [(x, -y) for x, y in reversed(poly_top)]
    base = DayBase([(round(x, 1), round(y, 1)) for x, y in da_giac], round(base_cao, 1))
    # tai bu lông móng (ベース耳): lỗ bu lông móng trên hình bằng nằm ngoài mép thân ベース.
    # Mép ngoài tai lấy từ đường đáy hình cạnh (chính xác hơn bóng raster).
    day_C = max([t for t in ngang(thC) if abs(t[0] - cz0) < 0.5], key=lambda t: t[2] - t[1])
    nua_C = (day_C[2] - day_C[1]) / 2

    def bac_tai(x):
        for x0_, x1_, r_ in bacs:
            if x0_ - 1 <= x <= x1_ + 1:
                return r_
        return bacs[0][2] if x < bacs[0][0] else bacs[-1][2]

    lo = [n for n in B.nets if n.kieu == "CIRCLE" and 10 <= 2 * n.ban_kinh <= 45
          and base_x0 <= n.tam[0] <= base_x1]
    hop = []
    tai = []
    co_tai = nua_C > max(b_[2] for b_ in bacs) + 3
    for n in lo:
        dy = abs(n.tam[1] - yc_B)
        sg = np.sign(n.tam[1] - yc_B)
        if co_tai and 0.6 * nua_C < dy < nua_C:
            if not any(abs(n.tam[0] - t[0]) < 1 and abs(dy - t[1]) < 1 and sg == t[3] for t in tai):
                tai.append((n.tam[0], dy, n.ban_kinh, np.sign(n.tam[1] - yc_B)))
    if tai:
        dd = [b_ - a_ for x, a_, b_, n in doc(thC, dai_min=3)
              if abs(abs(x - cy_side) - nua_C) < 1.0 and a_ - cz0 < 1.0 and b_ - cz0 < base_cao + 1]
        t_tai = min(dd) if dd else min(20.0, base_cao)
        if not dd:
            ghi.append("không đo được bề dày tai bu lông, lấy 20 mm")
        for x, dy, r_, sg in tai:
            w = 3.0 * r_
            prof = up if sg > 0 else dn
            vung = prof[(xs >= x - w) & (xs <= x + w)]
            ngoai = min(float(vung.max()), nua_C) if len(vung) else nua_C
            if abs(ngoai - nua_C) <= 1.5:
                ngoai = nua_C
            y0_, y1_ = sorted((sg * (bac_tai(x) - 5), sg * ngoai))
            hop.append(Hop(round(X(x - w), 1), round(X(x + w), 1), round(y0_, 1), round(y1_, 1), 0.0,
                           round(t_tai, 1), "ベース耳"))

    # ---- カップリングカバー (nét tưởng tượng)
    tu_D = D.loc("tuong")
    tu_B = B.loc("tuong")
    if tu_D:
        gx0, gz0, gx1, gz1 = bbox(tu_D)
        if tu_B:
            _, gy0, _, gy1 = bbox(tu_B)
            gy0, gy1 = gy0 - yc_B, gy1 - yc_B
        else:
            gy0, gy1 = -(gz1 - zc_D), (gz1 - zc_D)
        hop.append(Hop(X(gx0), X(gx1), gy0, gy1, gz0 - dz0, gz1 - dz0, "カップリングカバー"))
    else:
        gx0 = gx1 = None
        ghi.append("không thấy nét カップリングカバー")

    # ---- モータ: từ đầu trái đến カップリングカバー
    # Bề rộng trên hình bằng bị ベース che (ベース nằm dưới mọi thứ), nên bán kính lấy từ
    # phần nhô lên trên trục ở hình đứng; 端子箱 trên đỉnh là đoạn nhô vượt hẳn lên.
    bongD = lam_bong(thD)
    mx0 = dx0
    mx1 = gx0 if gx0 else dx0 + 0.45 * (dx1 - dx0)
    xs = np.arange(mx0 + 1, mx1 - 1, 1.0)
    lenD = _profile(bongD, xs, zc_D, +1)
    upB = _profile(bongB, xs, yc_B, +1)
    dnB = _profile(bongB, xs, yc_B, -1)
    R_m = float(np.median(lenD))
    hop_len = lenD > R_m + 25
    if hop_len.any():
        R_m = float(np.median(lenD[~hop_len]))
        hop_len = lenD > R_m + 25
    r_m = lenD.copy()
    r_m[hop_len] = R_m
    motor = [DoanTru(round(X(a), 1), round(X(b), 1), round(r, 1), "モータ") for a, b, r in _chia_bac(xs, r_m, sai=8, dai_min=20)
             if r > 5]
    if hop_len.sum() > 20:
        xa_ = xs[hop_len]
        a, b = float(xa_.min()), float(xa_.max())
        dinh = float(lenD[hop_len].max())
        w = min(0.75 * 2 * R_m, b - a)
        hop.append(Hop(X(a), X(b), -w / 2, w / 2, truc_z, truc_z + dinh, "端子箱", True))
    # 端子箱 ở cạnh: nhô ra ngoài mép ベース trên hình bằng
    nua_base = float(np.median(nua))
    for prof, s_ in ((upB, 1), (dnB, -1)):
        nho = prof - nua_base
        sel = nho > 15
        if sel.sum() > 50:
            xa_ = xs[sel]
            a, b = float(xa_.min()), float(xa_.max())
            dinh = float(prof[sel].max())
            y0_, y1_ = sorted((s_ * (R_m * 0.5), s_ * dinh))
            hop.append(Hop(X(a), X(b), y0_, y1_, truc_z - 0.7 * R_m, truc_z + 0.5 * R_m, "端子箱", True))
    # chân motor: hộp từ mặt trên ベース tới dưới thân motor
    if motor:
        ma0, ma1 = motor[0].x0, motor[-1].x1
        L = ma1 - ma0
        hop.append(Hop(ma0 + 0.2 * L, ma1 - 0.15 * L, -0.8 * R_m, 0.8 * R_m, base_cao, truc_z - 0.6 * R_m,
                       "モータ脚", True))

    # ---- phía bơm: từ sau カップリングカバー tới mặt bích hút
    px0 = gx1 if gx1 else mx1
    xs = np.arange(px0 + 1, xs_face - t_hut - 1, 1.0)
    r_p = _profile(bongD, xs, zc_D, +1)
    # bán kính vỏ ケーシング: nửa bề rộng bóng hình cạnh tại cao độ trục (lấy phía nhỏ hơn)
    bongC = lam_bong(thC)
    hangC = np.nonzero(bongC.hang(cz_side))[0]
    tr = cy_side - (bongC.x0 + hangC[0] * bongC.buoc)
    ph = bongC.x0 + hangC[-1] * bongC.buoc - cy_side
    R_vo = float(min(tr, ph))
    # quét từ mặt bích hút về phía motor: vỏ là đoạn liền có r >= 0.85 R_vo
    sel = r_p >= 0.85 * R_vo
    j = len(xs) - 1
    while j >= 0 and not sel[j]:
        j -= 1
    j1 = j
    while j >= 0 and sel[j]:
        j -= 1
    vx0, vx1 = xs[j + 1], xs[j1]
    ong = [DoanTru(round(X(a), 1), round(X(b), 1), round(r, 1), "ブラケット") for a, b, r in
           _chia_bac(xs[xs < vx0], r_p[xs < vx0], sai=5, dai_min=10) if r > 3]
    ong += [DoanTru(round(X(a), 1), round(X(b), 1), round(r, 1), "吸込ノズル") for a, b, r in
            _chia_bac(xs[xs > vx1], r_p[xs > vx1], sai=5, dai_min=5) if r > 3]

    # vỏ: đùn bóng hình cạnh (trên ベース, dưới đỉnh xoắn ốc), ống xả làm trụ riêng
    z_cat = min(truc_z + 1.15 * R_vo, ztop - dz0 - t_xa)
    vo = _vo_tu_hinh_canh(bongC, cy_side, cz0, base_cao + 2.0, z_cat)
    vo_lt = LangTru(round(X(vx0), 1), round(X(vx1), 1), vo, "ケーシング")
    # ống xả: nửa bề rộng bóng hình đứng ngay dưới mặt bích xả
    z_ong = ztop - t_xa - 8
    hangD = np.nonzero(bongD.hang(z_ong))[0]
    xs_h = bongD.x0 + hangD * bongD.buoc
    xs_h = xs_h[np.abs(xs_h - X0) < xa.D / 2]
    r_ong_xa = float(np.max(np.abs(xs_h - X0))) if len(xs_h) else xa.co * 0.6
    ong_xa = DoanTru(round(truc_z, 1), round(ztop - dz0 - t_xa, 1), round(min(r_ong_xa, xa.D / 2 - 5), 1), "吐出ノズル")
    return SoDoSJ(
        ma=ma, ban_ve=duong_dan_dxf.split("/")[-1], truc_z=round(truc_z, 1),
        dai_tong=round(dx1 - dx0, 1), cao_tong=round(dz1 - dz0, 1), base=base, hut=hut, xa=xa,
        motor=motor, hop=hop, ong_truc=ong, vo=vo_lt, ong_xa=ong_xa, R_vo=round(R_vo, 1), ghi_chu=ghi,
        goc_hinh={"dung": (X0, dz0), "bang": (X0, yc_B), "canh": (cy_side, cz0)},
    )


def _vo_tu_hinh_canh(bong, cy, cz0, z_duoi, z_tren, sai=1.5):
    """Đa giác (Y, Z) bao bóng hình cạnh trong dải z_duoi..z_tren."""
    from shapely.geometry import Polygon, MultiPolygon, box
    from shapely.ops import unary_union
    m = bong.mask
    H, W = m.shape
    # dựng đa giác từ các ô raster theo hàng (gộp đoạn liên tục)
    rects = []
    for i in range(H):
        z = bong.y0 + i * bong.buoc - cz0
        if z < z_duoi or z > z_tren:
            continue
        row = m[i]
        idx = np.nonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))[0]
        for a, b in zip(idx[::2], idx[1::2]):
            y0 = bong.x0 + a * bong.buoc - cy
            y1 = bong.x0 + b * bong.buoc - cy
            rects.append(box(y0, z, y1, z + bong.buoc))
    pg = unary_union(rects)
    if isinstance(pg, MultiPolygon):
        pg = max(pg.geoms, key=lambda p: p.area)
    pg = Polygon(pg.exterior).simplify(sai, preserve_topology=True)
    return [(round(x, 1), round(y, 1)) for x, y in list(pg.exterior.coords)[:-1]]


if __name__ == "__main__":
    import json
    import sys
    s = do_sj(sys.argv[1], sys.argv[2])
    print(json.dumps(s.to_dict(), ensure_ascii=False, indent=1))
