"""Lập bảng kê các zip bản vẽ テラル.

Nguồn vào (chọn một hoặc nhiều):
  --json FILE   Kết quả liệt kê file Drive dạng JSON {"files": [...]}.
                Nhận cả khóa của connector Claude (title, fileSize) lẫn của
                Drive API v3 (name, size). Có thể truyền nhiều file.
  --dir  FOLDER Thư mục テラル đã đồng bộ về máy bằng Google Drive for desktop.
                Id Drive đọc từ xattr nếu hệ điều hành có (macOS), không thì để trống.

Đầu ra:
  data/bang_ke_drive.csv   một dòng một zip
  data/bao_cao_ke.md       số theo dòng máy, file lệch mẫu, mã trùng

Chạy lại bao nhiêu lần cũng được; mỗi lần ghi đè hai file đầu ra.
Script chỉ đọc tên và metadata, không mở nội dung zip.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# テラル-<loại>-<số thứ tự>_<mã máy>.zip
TEN_FILE = re.compile(r"^テラル-(?P<loai>[^-_]+)-(?P<so>\d+)_(?P<ma>.+)\.zip$")
# Dòng máy = cụm chữ hoa đầu tiên của mã máy, bỏ tiền tố cỡ như "80", "8X6".
DONG_MAY = re.compile(r"^(?:\d+(?:X\d+)?)?(?P<dong>[A-Z]+)")

COT_CSV = [
    "ten_file",
    "loai",
    "so_thu_tu",
    "dong_may",
    "ma_may",
    "kich_thuoc_byte",
    "drive_id",
    "ghi_chu",
]


@dataclass
class Dong:
    ten_file: str
    kich_thuoc: int | None
    drive_id: str
    loai: str = ""
    so_thu_tu: str = ""
    dong_may: str = ""
    ma_may: str = ""
    ghi_chu: list[str] = field(default_factory=list)

    def hang_csv(self) -> dict:
        return {
            "ten_file": self.ten_file,
            "loai": self.loai,
            "so_thu_tu": self.so_thu_tu,
            "dong_may": self.dong_may,
            "ma_may": self.ma_may,
            "kich_thuoc_byte": "" if self.kich_thuoc is None else self.kich_thuoc,
            "drive_id": self.drive_id,
            "ghi_chu": ";".join(self.ghi_chu),
        }


def tach_ten(ten_file: str) -> dict | None:
    """Tách tên file theo mẫu. Trả None nếu lệch mẫu."""
    m = TEN_FILE.match(ten_file)
    if not m:
        return None
    ma = m["ma"]
    d = DONG_MAY.match(ma)
    return {
        "loai": m["loai"],
        "so_thu_tu": m["so"],
        "ma_may": ma,
        "dong_may": d["dong"] if d else "",
    }


def ghi_chu_ma(ma: str) -> list[str]:
    """Các điểm bất thường trong mã máy, không làm file bị coi là lệch mẫu."""
    notes = []
    if not ma.endswith("-e"):
        notes.append("e_giua_ma" if "-e" in ma else "khong_hau_to_e")
    return notes


def doc_json(path: Path) -> list[Dong]:
    data = json.loads(path.read_text(encoding="utf-8"))
    files = data["files"] if isinstance(data, dict) else data
    out = []
    for f in files:
        mime = f.get("mimeType", "")
        if mime == "application/vnd.google-apps.folder":
            continue
        if f.get("trashed"):
            continue
        ten = f.get("title") or f.get("name") or ""
        size = f.get("fileSize", f.get("size"))
        out.append(Dong(ten, int(size) if size not in (None, "") else None, f.get("id", "")))
    return out


def _xattr_id(p: Path) -> str:
    getx = getattr(os, "getxattr", None)
    names = ("com.google.drivefs.item-id#S", "user.drive.id")
    if getx is None:
        return ""
    for n in names:
        try:
            return getx(p, n).decode("utf-8", "replace").strip("\x00")
        except OSError:
            continue
    return ""


def doc_thu_muc(folder: Path) -> list[Dong]:
    out = []
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            out.append(Dong(p.name, p.stat().st_size, _xattr_id(p)))
    return out


def lap_bang(dongs: list[Dong]) -> tuple[list[Dong], int]:
    """Bỏ bản ghi trùng id (Drive search có thể trả trùng giữa các trang),
    tách tên, gắn ghi chú. Trả (danh sách, số bản ghi trùng đã bỏ)."""
    seen: set[str] = set()
    uniq: list[Dong] = []
    bo = 0
    for d in dongs:
        key = d.drive_id or d.ten_file
        if key in seen:
            bo += 1
            continue
        seen.add(key)
        uniq.append(d)

    for d in uniq:
        if not d.ten_file.lower().endswith(".zip"):
            d.ghi_chu.append("khong_phai_zip")
        t = tach_ten(d.ten_file)
        if t is None:
            d.ghi_chu.append("lech_mau")
            continue
        d.loai, d.so_thu_tu, d.dong_may, d.ma_may = (
            t["loai"], t["so_thu_tu"], t["dong_may"], t["ma_may"])
        if not d.dong_may:
            d.ghi_chu.append("khong_ro_dong_may")
        d.ghi_chu.extend(ghi_chu_ma(d.ma_may))

    theo_ma = defaultdict(list)
    theo_so = defaultdict(list)
    for d in uniq:
        if d.ma_may:
            theo_ma[d.ma_may].append(d)
            theo_so[d.so_thu_tu].append(d)
    for ds in theo_ma.values():
        if len(ds) > 1:
            for d in ds:
                d.ghi_chu.append("ma_trung")
    for ds in theo_so.values():
        if len(ds) > 1:
            for d in ds:
                d.ghi_chu.append("so_thu_tu_trung")

    uniq.sort(key=lambda d: (d.so_thu_tu or "~", d.ten_file))
    return uniq, bo


def ghi_csv(dongs: list[Dong], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COT_CSV)
        w.writeheader()
        for d in dongs:
            w.writerow(d.hang_csv())


def bao_cao(dongs: list[Dong], bo_trung: int, nguon: list[str]) -> str:
    hop_le = [d for d in dongs if d.ma_may]
    lech = [d for d in dongs if "lech_mau" in d.ghi_chu or "khong_phai_zip" in d.ghi_chu]
    dem_file = Counter(d.dong_may for d in hop_le)
    ma_theo_dong = defaultdict(set)
    for d in hop_le:
        ma_theo_dong[d.dong_may].add(d.ma_may)
    loai = Counter(d.loai for d in hop_le)

    L = []
    L.append("# Bảng kê zip テラル trên Drive")
    L.append("")
    L.append(f"Lập lúc {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC từ: {', '.join(nguon)}.")
    L.append("")
    L.append(f"- Tổng số file: **{len(dongs)}** (đã bỏ {bo_trung} bản ghi trùng id do Drive trả lặp).")
    L.append(f"- Khớp mẫu tên: {len(hop_le)}. Lệch mẫu: {len(lech)}.")
    L.append(f"- Số mã máy khác nhau: {len({d.ma_may for d in hop_le})}.")
    L.append(f"- Loại: " + ", ".join(f"{k} {v}" for k, v in loai.most_common()) + ".")
    L.append("")
    L.append("## Số theo dòng máy")
    L.append("")
    L.append("| Dòng máy | Số file | Số mã khác nhau |")
    L.append("|---|---:|---:|")
    for dong, n in sorted(dem_file.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"| {dong or '(không rõ)'} | {n} | {len(ma_theo_dong[dong])} |")
    L.append(f"| **Tổng** | **{sum(dem_file.values())}** | **{sum(len(s) for s in ma_theo_dong.values())}** |")
    L.append("")

    L.append("## File lệch mẫu tên")
    L.append("")
    if lech:
        for d in lech:
            L.append(f"- `{d.ten_file}` ({';'.join(d.ghi_chu)})")
    else:
        L.append("Không có file nào lệch mẫu `テラル-<loại>-<số>_<mã máy>.zip`.")
    L.append("")

    L.append("## Mã máy có dạng khác thường")
    L.append("")
    L.append("Vẫn khớp mẫu tên file, nhưng mã máy không kết thúc bằng `-e` như đa số.")
    L.append("")
    la = [d for d in hop_le if {"khong_hau_to_e", "e_giua_ma"} & set(d.ghi_chu)]
    for d in la:
        L.append(f"- `{d.ten_file}`")
    if not la:
        L.append("Không có.")
    L.append("")

    nhom = defaultdict(list)
    for d in hop_le:
        if "ma_trung" in d.ghi_chu:
            nhom[d.ma_may].append(d)
    L.append("## Mã máy xuất hiện ở nhiều số thứ tự")
    L.append("")
    L.append(f"{len(nhom)} mã, {sum(len(v) for v in nhom.values())} file. "
             "Kích thước khác nhau nên có thể là bản vẽ khác nhau (ví dụ 50/60 Hz); "
             "cần mở mẫu để biết. Chi tiết lọc cột `ghi_chu` = `ma_trung` trong CSV.")
    L.append("")
    L.append("| Mã máy | Số thứ tự (kích thước byte) |")
    L.append("|---|---|")
    for ma in sorted(nhom):
        ds = sorted(nhom[ma], key=lambda d: d.so_thu_tu)
        L.append(f"| {ma} | " + ", ".join(f"{d.so_thu_tu} ({d.kich_thuoc})" for d in ds) + " |")
    L.append("")

    trung_so = defaultdict(list)
    for d in hop_le:
        if "so_thu_tu_trung" in d.ghi_chu:
            trung_so[d.so_thu_tu].append(d.ten_file)
    if trung_so:
        L.append("## Số thứ tự bị dùng cho nhiều file")
        L.append("")
        for so, ts in sorted(trung_so.items()):
            L.append(f"- {so}: " + ", ".join(f"`{t}`" for t in ts))
        L.append("")

    so = sorted(int(d.so_thu_tu) for d in hop_le)
    if so:
        thieu = sorted(set(range(so[0], so[-1] + 1)) - set(so))
        L.append("## Khoảng trống số thứ tự")
        L.append("")
        L.append(f"Số thứ tự từ {so[0]:04d} đến {so[-1]:04d}. Thiếu {len(thieu)} số"
                 + (": " + ", ".join(f"{x:04d}" for x in thieu) if thieu else "") + ".")
        L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="append", default=[], type=Path)
    ap.add_argument("--dir", action="append", default=[], type=Path)
    ap.add_argument("--csv", type=Path, default=Path("data/bang_ke_drive.csv"))
    ap.add_argument("--bao-cao", type=Path, default=Path("data/bao_cao_ke.md"))
    ap.add_argument("--so-mong-doi", type=int, help="Số file đếm độc lập trên Drive; lệch thì thoát mã 1.")
    a = ap.parse_args(argv)
    if not a.json and not a.dir:
        ap.error("cần --json hoặc --dir")

    raw: list[Dong] = []
    for p in a.json:
        raw += doc_json(p)
    for p in a.dir:
        raw += doc_thu_muc(p)
    dongs, bo = lap_bang(raw)
    ghi_csv(dongs, a.csv)
    a.bao_cao.parent.mkdir(parents=True, exist_ok=True)
    a.bao_cao.write_text(bao_cao(dongs, bo, [p.name for p in a.json + a.dir]) + "\n", encoding="utf-8")
    print(f"{len(dongs)} file -> {a.csv}, báo cáo -> {a.bao_cao}")
    if a.so_mong_doi is not None and a.so_mong_doi != len(dongs):
        print(f"LỆCH: Drive có {a.so_mong_doi} file, bảng kê có {len(dongs)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
