"""Ghép mô hình 3D dòng SJ từ số đo (SoDoSJ) và sinh 接続口.

Quy ước hình dạng (mức chi tiết, cách chia khối) để ở đây cho dễ thay khi có luật dựng hình chung.
"""
from __future__ import annotations

from .geom import Luoi, hop, lang_tru, tru
from .ifc_rebro import DauNoi
from .sj import SoDoSJ

N_TRU = 24          # số cạnh trụ
N_TRU_NHO = 16


def dung_sj(s: SoDoSJ) -> list[Luoi]:
    m: list[Luoi] = []
    zc = s.truc_z
    # ベース
    m.append(lang_tru(s.base.da_giac, 0.0, s.base.cao, "z", "ベース"))
    # モータ
    for d in s.motor:
        m.append(tru(d.r, d.x0, d.x1, "x", (0.0, zc), N_TRU, "モータ"))
    # hộp: カバー, 端子箱, chân motor
    for h in s.hop:
        m.append(hop(h.x0, h.x1, h.y0, h.y1, h.z0, h.z1, h.ten))
    # ブラケット, 吸込ノズル
    for d in s.ong_truc:
        m.append(tru(d.r, d.x0, d.x1, "x", (0.0, zc), N_TRU, d.ten))
    # ケーシング
    if s.vo:
        m.append(lang_tru(s.vo.da_giac, s.vo.x0, s.vo.x1, "x", "ケーシング"))
    # 吸込: ống nối từ vỏ tới mặt bích, rồi mặt bích
    hx = s.hut.tam[0]
    sau_bich = hx - s.hut.t
    if s.vo and sau_bich - s.vo.x1 > 1:
        r = min(s.hut.co / 2 + 0.1 * s.hut.co + 5, s.hut.D / 2 - 5)
        m.append(tru(r, s.vo.x1, sau_bich, "x", (0.0, zc), N_TRU, "吸込ノズル"))
    m.append(tru(s.hut.D / 2, sau_bich, hx, "x", (0.0, zc), N_TRU, "吸込フランジ"))
    # 吐出: ống đứng + mặt bích
    zf = s.xa.tam[2]
    if s.ong_xa:
        m.append(tru(s.ong_xa.r, s.ong_xa.x0, s.ong_xa.x1, "z", (0.0, 0.0), N_TRU, "吐出ノズル"))
    m.append(tru(s.xa.D / 2, zf - s.xa.t, zf, "z", (0.0, 0.0), N_TRU, "吐出フランジ"))
    return m


def dau_noi_sj(s: SoDoSJ, ma_hut: str = "A20", ma_xa: str = "A20") -> list[DauNoi]:
    """接続口: tâm mặt ngoài フランジ, hướng ra ngoài. Thứ tự: 吸込 rồi 吐出."""
    return [
        DauNoi(tuple(s.hut.tam), s.hut.co, tuple(s.hut.huong), ma_hut),
        DauNoi(tuple(s.xa.tam), s.xa.co, tuple(s.xa.huong), ma_xa),
    ]
