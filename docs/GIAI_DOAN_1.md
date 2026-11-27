# Giai đoạn 1: 5 mã SJ nhập Rebro

## 5 mã đã chọn (50Hz)

| Vai trò | Mã | Zip (số thứ tự) | DXF | Kiểu DXF |
|---|---|---|---|---|
| nhỏ nhất | SJ32X32L5.75-e | 0527 | PC4-13978-0 | AC1015 |
| lớn nhất | SJ4-200X150J575-e | 0823 (0824 cùng 外形図) | PC4-17209-1 | AC1015 |
| ngẫu nhiên | SJ100X80K545-e | 0640 (0642 cùng 外形図) | PC4-14040-1 | AC1015 |
| ngẫu nhiên | SJ4-150X125J530-e | 0783 (0785 cùng 外形図) | PC4-14087-1 | AC1015 |
| ngẫu nhiên | SJ4S-150X125J530-e | 0855 | a04835 | AC1009 (kiểu cũ) |

Chọn ngẫu nhiên bằng `random.seed(20261127)` trên 108 mã SJ/SJ4/SJ4S có đuôi `-e` và không có hậu tố `H`. Các zip trùng mã (cùng mã, khác số thứ tự) có chung 外形図 và 構造図, chỉ khác file 特性曲線 `*_pr-*.pdf`, nên chỉ cần dựng một lần.

## Cách làm

1. **Đọc DXF** (`buzai/dxf_doc.py`): làm phẳng LINE/ARC/CIRCLE/ELLIPSE/POLYLINE/INSERT thành polyline, phân loại nét theo layer hoặc linetype: thấy (T01, T02), tâm (T06), khuất (T05), tưởng tượng (T08). Chạy được cả DXF kiểu mới và kiểu cũ.
2. **Tách 3 hình chiếu** (`buzai/views.py`): gom cụm nét thấy theo khoảng cách (khe 8 mm). Hình đứng và hình bằng thẳng cột; hình cạnh nằm ngang hàng hình đứng, bên phải.
3. **Đo** (`buzai/sj.py`), toạ độ mô hình: X dọc trục bơm (モータ sang ポンプ), Z lên, Z = 0 ở đáy ベース, gốc X/Y tại tâm 吐出フランジ.
   - Trục bơm: tâm nhóm tròn đồng tâm lớn nhất ở hình cạnh (mặt bích hút).
   - 吐出フランジ: nhóm tròn đồng tâm ở hình bằng cho tâm và đường kính; đỉnh nét thấy ở hình đứng cho cao độ mặt bích.
   - 吸込フランジ: mép phải hình đứng cho vị trí mặt bích; đường kính lấy từ hình cạnh.
   - Đường kính mặt bích được ép về JIS B 2220 10K gần nhất (`buzai/chuan.py`), ưu tiên cỡ ghi trong mã máy.
   - ベース: dài theo đường đáy hình đứng; cao theo đường ngang chạy suốt (ベース kênh thép) hoặc đường ngang cao nhất ở phần dưới (ベース đúc); rộng theo từng bậc trên hình bằng; tai bu lông móng (ベース耳) lấy từ lỗ bu lông trên hình bằng và đường đáy hình cạnh.
   - カップリングカバー: khung nét tưởng tượng T08 ở hình đứng và hình bằng.
   - モータ: bán kính theo bóng hình đứng phía trên trục, chia bậc. 端子箱 là đoạn nhô vượt bán kính motor (trên đỉnh), hoặc nhô ra ngoài mép ベース trên hình bằng (ở cạnh).
   - ブラケット: bán kính theo bóng hình đứng, chia bậc.
   - ケーシング: bóng hình cạnh (phần trên ベース, dưới đỉnh xoắn ốc) đùn theo X.
4. **Dựng hình** (`buzai/mo_hinh_sj.py`, `buzai/geom.py`): hộp, trụ 24 cạnh, lăng trụ. Không ren, không bo góc. Quy ước hình dạng gom ở `mo_hinh_sj.py` để dễ thay khi áp luật dựng hình chung.
5. **Ghi IFC** (`buzai/ifc_rebro.py`): IFC4, `IfcDistributionElement`, hình qua `IfcMappedItem` chứa `IfcTriangulatedFaceSet` (tuỳ chọn `--hinh brep` để ghi `IfcFacetedBrep`), các pset `BSJ_MEP_Common`, `BSJ_MEP_EquipmentCommon`, `BSJ_MEP_EquipmentData`, `BSJ_MEP_EstimateData` theo đúng mẫu Rebro.

Chạy:

```bash
python tools/dung_sj.py --zip "G:\My Drive\テラル\テラル-陸上ポンプ-0527_SJ32X32L5.75-e.zip" --ra ifc_out
python tools/ve_lai.py <file.dxf> <mã> anh.png      # vẽ lại 3 hình chiếu chồng lên DXF
python tools/kiem_sj.py ifc_out                       # so với số PDF trong data/sj_so_pdf.csv
```

## 接続口

Theo 2 file mẫu do Rebro 2026 xuất (`tests/mau_rebro/`), 接続口 là text trong `BSJ_MEP_Common.connecting_point_1..4`. Mỗi đầu nối 14 trường:

```
x, y, z, cỡ(A), 0, 0, mã, 0, hx, hy, hz, 0, 0, 0
```

Toạ độ là toạ độ thế giới (mm), vector hướng ra ngoài. Các đầu nối cùng nhóm nối tiếp bằng dấu phẩy. Cả hai mẫu Rebro đều dùng nhóm 2 và mã `A20`. Bơm SJ ghi 2 đầu nối vào nhóm 2: 吸込 (hướng +X) rồi 吐出 (hướng +Z), cỡ theo 呼び径 của mặt bích.

Chưa rõ: cả 4 mẫu ねじ込み/フランジ đều ghi `A20` và các trường còn lại như nhau, nên chưa biết cách ghi kiểu nối. Tạm ghi `A20` cho mọi 接続口. Mẫu 80Aフランジ trong `setsuzoku.ifc` ghi nhầm cỡ 50; bản trong repo đã sửa thành 80 theo xác nhận của người dùng.

`CGRYCODE` (機器分類コード) tạm dùng `50908000000000` (その他特殊設備) như mẫu; chưa có mã phân loại riêng cho ポンプ.

## Tự kiểm

- 35/35 kích thước có số ghi trên PDF (dài ベース, rộng ベース, cao trục, cao mặt bích xả, vị trí mặt bích hút, đường kính 2 mặt bích) khớp trong 1 mm. Số PDF đọc bằng mắt, lưu ở `data/sj_so_pdf.csv`.
- IFC qua `ifcopenshell.validate` không lỗi. 1.200 đến 1.900 tam giác mỗi mã (trần 5.000).

## Giới hạn đã biết

- Bề dày tai bu lông và phần ベース đúc có bậc (dưới motor) dựng gần đúng: ベース là tấm phẳng, phần cao dưới motor do khối モータ脚 lấp.
- ケーシング là lăng trụ đùn từ hình cạnh nên ở hình đứng là khối chữ nhật, rộng hơn vỏ thật ở phần trên.
- 端子箱 và モータ脚: bề rộng theo phương còn lại là ước lượng (đánh dấu `uoc_luong` trong JSON).
- SJ32X32L5.75-e: 端子箱 trên hình bằng che một lỗ bu lông móng nên chỉ dựng 3/4 tai.
- Hình cạnh của DXF テラル không vẽ モータ, nên khi so hình cạnh, motor và 端子箱 của mô hình lộ ra phía sau là bình thường.
