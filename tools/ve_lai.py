"""Vẽ lại 3 hình chiếu từ mô hình, chồng lên nét DXF gốc để so (PNG)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

from buzai.dxf_doc import doc_ban_ve  # noqa: E402
from buzai.geom import gop  # noqa: E402
from buzai.mo_hinh_sj import dung_sj  # noqa: E402
from buzai.sj import do_sj  # noqa: E402
from buzai.views import tach_hinh_chieu  # noqa: E402


def ve(dxf: str, ma: str, out: str):
    s = do_sj(dxf, ma)
    m = gop(dung_sj(s))
    h = tach_hinh_chieu(doc_ban_ve(dxf))
    fig, axs = plt.subplots(1, 3, figsize=(27, 8), gridspec_kw={"width_ratios": [3, 3, 1.4]})
    cfg = [("bang", h.bang, (0, 1), "hình bằng (X-Y)"), ("dung", h.dung, (0, 2), "hình đứng (X-Z)"),
           ("canh", h.canh, (1, 2), "hình cạnh từ phía hút (Y-Z)")]
    for ax, (k, cum, (i, j), tit) in zip(axs, cfg):
        tris = m.v[m.f][:, :, [i, j]]
        ax.add_collection(PolyCollection(tris, facecolor="#9cc3e6", edgecolor="none", alpha=0.55))
        gx, gy = s.goc_hinh[k]
        for n in cum.nets:
            if n.loai in ("thay", "tuong"):
                ax.plot(n.diem[:, 0] - gx, n.diem[:, 1] - gy, "k" if n.loai == "thay" else "g", lw=0.4)
        ax.set_aspect("equal")
        ax.autoscale()
        ax.set_title(tit)
        ax.grid(lw=0.2)
    for d in [s.hut, s.xa]:
        x, y, z = d.tam
        hx, hy, hz = d.huong
        L = 80
        axs[1].annotate("", (x + hx * L, z + hz * L), (x, z), arrowprops=dict(color="r", width=1.5))
        axs[0].plot([x], [y], "r^")
    fig.suptitle(f"{ma}  ({s.ban_ve})  xanh = mô hình, đen = DXF, đỏ = 接続口")
    fig.savefig(out, dpi=80, bbox_inches="tight")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("ma")
    ap.add_argument("out")
    a = ap.parse_args()
    ve(a.dxf, a.ma, a.out)
