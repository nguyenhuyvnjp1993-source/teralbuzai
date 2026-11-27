# teralbuzai

Thư viện hàm sinh hình 3D có tham số cho máy テラル, xuất IFC nhập được vào Rebro, cùng hệ với thư viện 部材 HuyMeAI (`BSJ_MEP_*`).

Các quyết định đã chốt nằm trong [docs/HANDOFF.md](docs/HANDOFF.md). Đọc file đó trước khi làm bất cứ việc gì.

## Repo chứa gì

| Thư mục | Nội dung |
|---|---|
| `docs/` | HANDOFF, hướng dẫn cài |
| `tools/` | Script tiện ích (bảng kê Drive...) |
| `tests/` | Kiểm thử |
| `data/` | Bảng kê, bảng tham số do code trích ra |

Repo **không** chứa bản vẽ gốc (zip, DXF, PDF) và **không** chứa IFC sinh ra. Bản vẽ gốc nằm trên Google Drive, thư mục `テラル`, đồng bộ về máy bằng Google Drive for desktop.

## Cài đặt

Xem [docs/CAI_DAT.md](docs/CAI_DAT.md).

## Bảng kê bản vẽ trên Drive (giai đoạn 0)

Kết quả hiện tại: [data/bang_ke_drive.csv](data/bang_ke_drive.csv) và [data/bao_cao_ke.md](data/bao_cao_ke.md).

Cột của CSV: `ten_file, loai, so_thu_tu, dong_may, ma_may, kich_thuoc_byte, drive_id, ghi_chu`. Cột `ghi_chu` có thể chứa:

- `lech_mau`: tên không theo mẫu `テラル-<loại>-<số>_<mã máy>.zip`
- `khong_phai_zip`: file không phải zip
- `khong_hau_to_e`, `e_giua_ma`: mã máy không kết thúc bằng `-e`
- `ma_trung`: cùng mã máy xuất hiện ở nhiều số thứ tự
- `so_thu_tu_trung`: cùng số thứ tự cho nhiều file

### Chạy lại khi tải thêm bản vẽ

Script chỉ đọc tên và metadata, không mở zip. Có hai cách:

**Cách 1: nhờ Claude.** Nói "kê lại Drive テラル". Claude liệt kê thư mục qua connector Google Drive, lưu JSON vào `data/raw/` (không commit), rồi chạy:

```bash
python tools/ke_drive.py --json data/raw/drive.json --so-mong-doi <số file Drive báo>
```

**Cách 2: tự chạy trên máy** từ thư mục đã đồng bộ:

```bash
python tools/ke_drive.py --dir "G:\My Drive\テラル"
```

Trên macOS, id Drive được đọc từ thuộc tính mở rộng của Drive for desktop. Trên Windows cột `drive_id` để trống.

`--so-mong-doi N` làm script thoát mã 1 nếu bảng kê không đúng N file, dùng để đối chiếu với số Drive hiển thị.

## Kiểm thử

```bash
python -m pytest -q
```
