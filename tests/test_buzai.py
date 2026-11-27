import os
import re
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as ue
import numpy as np
import pytest

from buzai.chuan import JIS10K, flange_gan_nhat
from buzai.geom import gop, hop, lang_tru, tru
from buzai.ifc_rebro import DauNoi, ThongTinBuzai, ghi_ifc
from buzai.sj import _chia_bac, co_tu_ma

MAU = Path(__file__).parent / "mau_rebro"


def the_tich(m):
    v, f = m.v, m.f
    return np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6


def kin(m):
    """Mỗi cạnh có đúng 2 tam giác dùng chung, ngược chiều."""
    canh = {}
    for t in m.f:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            canh[(a, b)] = canh.get((a, b), 0) + 1
    return all(canh.get((b, a), 0) == 1 and c == 1 for (a, b), c in canh.items())


def test_hop():
    m = hop(0, 10, 0, 20, 0, 30)
    assert m.so_tam_giac == 12 and kin(m)
    assert the_tich(m) == pytest.approx(6000)


@pytest.mark.parametrize("truc", ["x", "y", "z"])
def test_tru(truc):
    m = tru(50, 0, 100, truc, (0, 0), 64)
    assert kin(m)
    assert the_tich(m) == pytest.approx(np.pi * 50 ** 2 * 100, rel=0.01)
    lo, hi = m.bbox()
    k = "xyz".index(truc)
    assert lo[k] == pytest.approx(0) and hi[k] == pytest.approx(100)


def test_lang_tru_chu_L():
    m = lang_tru([(0, 0), (20, 0), (20, 10), (10, 10), (10, 30), (0, 30)], 0, 5, "x")
    assert kin(m)
    assert the_tich(m) == pytest.approx((20 * 10 + 10 * 20) * 5)


def test_flange():
    co, tt, lech = flange_gan_nhat(184.6, 80)
    assert co == 80 and tt[0] == 185
    co, tt, _ = flange_gan_nhat(331)
    assert co == 200
    assert JIS10K[32][:2] == (135, 100)


def test_co_tu_ma():
    assert co_tu_ma("SJ4-150X125J530-e") == (150, 125)
    assert co_tu_ma("SJ32X32L5.75-e") == (32, 32)


def test_chia_bac():
    xs = np.arange(0, 300, 1.0)
    r = np.where(xs < 100, 50, np.where(xs < 110, 80, 60)).astype(float)
    bac = _chia_bac(xs, r, sai=4, dai_min=20)
    assert [round(b[2]) for b in bac] == [50, 60]


def _cp_mau():
    f = ifcopenshell.open(str(MAU / "setsuzoku.ifc"))
    return [ue.get_psets(e)["BSJ_MEP_Common"]["connecting_point_2"] for e in f.by_type("IfcDistributionElement")]


def test_dinh_dang_dau_noi_giong_rebro():
    """Chuỗi 接続口 phải cùng khuôn với file Rebro xuất: nhóm 14 trường, trường 7 là mã."""
    khuon = re.compile(r"^-?\d+\.\d{6},-?\d+\.\d{6},-?\d+\.\d{6},\d+,0,0,A\d+,0,(-?\d+\.\d{6},){5}-?\d+\.\d{6}$")
    for s in _cp_mau():
        truong = s.split(",")
        assert len(truong) % 14 == 0
        for i in range(0, len(truong), 14):
            assert khuon.match(",".join(truong[i:i + 14]))
    d = DauNoi((100, 0, 320), 100, (1, 0, 0)).chuoi()
    assert khuon.match(d)


def test_mau_80A_da_sua():
    cps = _cp_mau()
    assert all(",80,0,0," in s for s in cps if s.startswith("5795."))


def test_ghi_ifc(tmp_path):
    m = [hop(0, 100, -50, 50, 0, 80), tru(20, 100, 150, "x", (0, 40))]
    tt = ThongTinBuzai("SJ型渦巻ポンプ", "SJTEST-e",
                       dau_noi=[DauNoi((150, 0, 40), 32, (1, 0, 0)), DauNoi((50, 0, 80), 32, (0, 0, 1))])
    p = tmp_path / "t.ifc"
    ghi_ifc(str(p), tt, m)
    f = ifcopenshell.open(str(p))
    el = f.by_type("IfcDistributionElement")
    assert len(el) == 1
    ps = ue.get_psets(el[0])
    cp = ps["BSJ_MEP_Common"]["connecting_point_2"].split(",")
    assert len(cp) == 28 and cp[3] == "32" and cp[6] == "A20"
    assert ps["BSJ_MEP_Common"]["connecting_point_1"] == ""
    assert el[0].Representation.Representations[0].Items[0].is_a("IfcMappedItem")
    tri = sum(len(i.CoordIndex) for i in f.by_type("IfcTriangulatedFaceSet"))
    assert tri == sum(x.so_tam_giac for x in m)


DXF_DIR = os.environ.get("TERAL_DXF_DIR")


@pytest.mark.skipif(not DXF_DIR, reason="đặt TERAL_DXF_DIR=thư mục chứa DXF mẫu để chạy")
def test_sj_tu_dxf():
    from buzai.mo_hinh_sj import dung_sj
    from buzai.sj import do_sj
    s = do_sj(str(Path(DXF_DIR) / "PC4-14040-1.dxf"), "SJ100X80K545-e")
    assert s.truc_z == pytest.approx(320, abs=1)
    assert s.xa.tam[2] == pytest.approx(570, abs=1)
    assert s.hut.tam[0] == pytest.approx(100, abs=1)
    assert sum(m.so_tam_giac for m in dung_sj(s)) <= 5000
