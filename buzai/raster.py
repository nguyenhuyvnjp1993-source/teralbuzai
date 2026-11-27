"""Raster hoá nét thấy của một hình chiếu thành mặt nạ bóng (silhouette)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from .dxf_doc import Net


@dataclass
class Bong:
    """Mặt nạ bóng: mask[i, j] ứng với điểm (x0 + j*buoc, y0 + i*buoc)."""
    mask: np.ndarray
    x0: float
    y0: float
    buoc: float

    def cot(self, x: float) -> np.ndarray:
        j = int(round((x - self.x0) / self.buoc))
        j = min(max(j, 0), self.mask.shape[1] - 1)
        return self.mask[:, j]

    def tam_y(self, x: float):
        """(y thấp nhất, y cao nhất) của bóng tại cột x, hoặc None."""
        c = np.nonzero(self.cot(x))[0]
        if len(c) == 0:
            return None
        return self.y0 + c[0] * self.buoc, self.y0 + c[-1] * self.buoc

    def hang(self, y: float) -> np.ndarray:
        i = int(round((y - self.y0) / self.buoc))
        i = min(max(i, 0), self.mask.shape[0] - 1)
        return self.mask[i, :]


def lam_bong(nets: list[Net], buoc: float = 1.0, le: float = 10.0, day: int = 2) -> Bong:
    a = np.array([n.bbox for n in nets])
    x0, y0 = a[:, 0].min() - le, a[:, 1].min() - le
    x1, y1 = a[:, 2].max() + le, a[:, 3].max() + le
    W = int(np.ceil((x1 - x0) / buoc)) + 1
    H = int(np.ceil((y1 - y0) / buoc)) + 1
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for n in nets:
        p = [((x - x0) / buoc, (y - y0) / buoc) for x, y in n.diem]
        d.line(p, fill=255, width=day)
    ImageDraw.floodfill(img, (0, 0), 128)
    m = np.array(img) != 128
    # bù độ dày nét: nét vẽ rộng `day` px, bóp lại nửa nét
    return Bong(m, x0, y0, buoc)
