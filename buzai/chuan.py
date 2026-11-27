"""Bảng tiêu chuẩn: フランジ JIS B 2220 10K (並形)."""
from __future__ import annotations

# 呼び径 A -> (D ngoài, C vòng bu lông, t chiều dày, số lỗ, d lỗ)
JIS10K = {
    10: (90, 65, 12, 4, 15),
    15: (95, 70, 12, 4, 15),
    20: (100, 75, 14, 4, 15),
    25: (125, 90, 14, 4, 19),
    32: (135, 100, 16, 4, 19),
    40: (140, 105, 16, 4, 19),
    50: (155, 120, 16, 4, 19),
    65: (175, 140, 18, 4, 19),
    80: (185, 150, 18, 8, 19),
    100: (210, 175, 18, 8, 19),
    125: (250, 210, 20, 8, 23),
    150: (280, 240, 22, 8, 23),
    200: (330, 290, 22, 12, 23),
    250: (400, 355, 24, 12, 25),
    300: (445, 400, 24, 16, 25),
}


def flange_gan_nhat(D_do: float, co_goi_y: int | None = None):
    """Ép về cỡ JIS 10K gần nhất theo đường kính ngoài đo được.

    Trả (cỡ, thông số, độ lệch). Nếu có cỡ gợi ý (từ mã máy) thì ưu tiên cỡ đó khi lệch <= 2 mm.
    """
    if co_goi_y in JIS10K and abs(JIS10K[co_goi_y][0] - D_do) <= 2.0:
        return co_goi_y, JIS10K[co_goi_y], JIS10K[co_goi_y][0] - D_do
    co = min(JIS10K, key=lambda k: abs(JIS10K[k][0] - D_do))
    return co, JIS10K[co], JIS10K[co][0] - D_do
