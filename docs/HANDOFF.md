# Thư viện 部材 テラル cho Rebro: các quyết định đã chốt

File này ghi lại kết quả buổi thống nhất kế hoạch ngày 2026-11-27. Phiên làm việc mới trên repo riêng đọc file này trước khi bắt đầu, không hỏi lại những điều đã chốt.

## Mục tiêu

Xây thư viện hàm sinh hình 3D có tham số cho các máy của テラル, xuất ra IFC nhập được vào Rebro, cùng hệ với thư viện 部材 HuyMeAI (file `BSJ_MEP_*`). Tổng quy mô khoảng 25.000 mã máy.

Lý do dựng lại thay vì dùng mô hình hãng: mô hình hãng quá chi tiết nên nặng, và không tải thẳng được.

## Phạm vi

- Chỉ làm cấu kiện thuộc máy テラル.
- Chỉ dựng phần nhìn thấy từ bên ngoài. Bỏ chi tiết bên trong vỏ máy (羽根車, 主軸, メカニカルシール, ボールベアリング...).
- Bài toán A làm trước: dựng thư viện từ bộ bản vẽ đã tải, mã máy đã biết qua tên file.
- Bài toán B làm sau: nhận bản vẽ 3 hình chiếu không rõ mã rồi khớp vào dòng máy đã có. Chỉ bắt đầu khi A đã phủ đủ rộng.

## Nguồn dữ liệu

- Bản vẽ テラル nằm trên Google Drive, thư mục `テラル` (id `1Mmwv-zGpEOdyEQ7oJZc-AHMmmmETkk74`). Người dùng tự tải từ trang テラル và còn đang tải thêm. Bản vẽ gốc không đưa vào git.
- Tên file: `テラル-<loại>-<số thứ tự>_<mã máy>.zip`.
- Mỗi zip gồm: `pc4-*.pdf` (外形寸法図), `ps4-*.pdf` (内部構造図 kèm bảng bộ phận), một DXF của 外形図, và ở một số dòng có `*_pr-*.pdf` (特性曲線). Không có 分解図.
- 3dfindit không phải nguồn dữ liệu. Người dùng tự xem bằng mắt để đối chiếu độ đủ bộ phận. Claude không đọc tự động và không nhận file tải từ đó (điều khoản của CADENAS có vẻ cấm dùng cho AI; chưa đọc được toàn văn).
- Cấu kiện tiêu chuẩn (フランジ...) lấy kích thước từ bảng JIS. Chuẩn フランジ テラル dùng chưa được xác minh, phải đọc từ 外形寸法図 trước khi viết hàm.

### Kiểm kê tạm thời (994 file, ngày 2026-11-27, chưa đủ)

Tất cả thuộc 陸上ポンプ. Số mã theo dòng: SJ 329, LS 159, M 102, MSP 49, MKHS 45, LP 44, SM 38, SKJ 33, LPE 30, SLP 26, NX 20, NXH 20, SJM 20, SJMS 18, SLF 16, SMF 11, SHF 11, SJS 10, MTP 5, ESPM 4, SKF 3, LPS 1. Phải kiểm kê lại khi người dùng báo đã tải đủ.

### Đặc điểm file (từ 6 zip mẫu)

- DXF chỉ có nét vẽ hình ở tỷ lệ 1:1 mm (suy ra từ một mẫu SJ). Không có DIMENSION, không có bảng kích thước. DXF tự ghi chú rằng hình có thể chứa phần giản lược sai kích thước.
- DXF kiểu mới (SJ, M): AC1015, cp932, layer theo loại nét (`T02--Continuous_25` là nét thấy, `T05--Dashed`, `T06--...` là đường tâm).
- DXF kiểu cũ (SM, LP): AC1009, một layer `M0`, loại nét nằm ở linetype của từng entity, không khai báo đơn vị.
- Ba hình chiếu không tách theo layer hay block; tách được bằng gom cụm theo khoảng cách (khe hở khoảng 15 mm).
- PDF là vector nhưng chữ là nét vẽ, không trích được text. Muốn lấy số phải đọc bằng hình ảnh.
- Bảng bộ phận của 構造図 chỉ tả đầu bơm. モータ, 共通ベース, カップリング chỉ thấy trên 外形図.

## Cách dựng

- Mỗi loại cấu kiện là một hàm sinh hình có tham số, có kiểm thử.
- Mỗi dòng máy có một hàm ghép. Mỗi mã máy là một dòng trong bảng tham số do code trích tự động.
- Danh sách cấu kiện của một dòng máy lấy từ bảng bộ phận 構造図 (phần thấy từ ngoài) cộng với những gì thấy trên 外形図.
- Hình dạng và tỷ lệ đo trên DXF. Số ghi trên PDF dùng để kiểm lại; khi lệch nhau thì PDF thắng. Mã không có PDF thì đo theo DXF.
- Phần không có số ghi thì dựng theo tỷ lệ đo trên hình và đánh dấu là ước lượng.
- Cấu kiện tiêu chuẩn được ép về cỡ gần nhất trong bảng tiêu chuẩn và ghi lại việc ép.
- Hình dựng bằng khối cơ bản (trụ, hộp, nón, khối xoay). ポリメッシュ là dạng xuất ra IFC. Trần 5.000 tam giác cho mỗi 部材.
- Mức chi tiết như 部材 của Rebro: không ren, không bo góc.
- Công nghệ: Python, `ezdxf` để đọc DXF, `ifcopenshell` để ghi IFC.

## Tiêu chí đạt

Một 部材 đạt khi:
1. Nhập vào Rebro không lỗi.
2. Kích thước có ghi số lệch không quá 1 mm.
3. Ống hoặc ダクト trong Rebro nối được vào 接続口, đúng cỡ và đúng hướng.
4. Có đủ mọi bộ phận trong danh sách bắt buộc của dòng máy. Người dùng duyệt danh sách này một lần sau khi so với 3dfindit.

## Kiểm tra ở quy mô 25.000 mã

- Claude tự kiểm: kích thước bao, vị trí 接続口, số mặt, và vẽ lại 3 hình chiếu từ mô hình để so với DXF gốc.
- Mỗi dòng máy đọc PDF cho 5 mã (nhỏ nhất, lớn nhất, 3 ngẫu nhiên). Cả 5 khớp DXF trong 1 mm thì các mã còn lại tin theo DXF.
- Mỗi dòng máy người dùng nhập 3 mã vào Rebro. Người dùng quyết định cuối.
- Mã không qua kiểm tự động thì loại khỏi thư viện và đưa vào danh sách chờ. Không sửa tay từng mã; chỉ sửa hàm của dòng máy khi cả nhóm hỏng cùng kiểu.

## Nơi chạy và lưu trữ

- Repo riêng tư do người dùng tạo, tách khỏi `quanlychitieu`. Repo này cũng là nơi chứa thư viện 部材 HuyMeAI (gộp phần học từ IFC Rebro và phần sinh hình).
- Repo chỉ chứa code, bảng tham số và hướng dẫn. Không chứa bản vẽ gốc, không chứa IFC sinh ra.
- Bản vẽ gốc đồng bộ về máy người dùng bằng Google Drive for desktop.
- Claude phát triển hàm trên repo với vài mã mẫu mỗi dòng.
- Lô dựng đầy đủ do người dùng chạy trên máy mình bằng một lệnh, ghi IFC ra ổ cứng. Máy cần Python, `ezdxf`, `ifcopenshell`; repo phải có hướng dẫn cài.
- IFC chỉ sinh cho dòng máy đang cần, không giữ sẵn cả 25.000 file.

## Các giai đoạn

| # | Việc | Điều kiện qua |
|---|---|---|
| 0 | Tạo repo; lập bảng kê toàn bộ zip trên Drive | Bảng kê khớp số file trên Drive |
| 1 | Làm trọn 5 mã dòng SJ: tách 3 hình chiếu, đo, sinh hình, ghi IFC kèm 接続口 | Người dùng nhập 5 file vào Rebro và đạt cả 4 tiêu chí |
| 2 | Tách cấu kiện dùng chung thành thư viện có kiểm thử (フランジ, モータ kèm 端子箱, ベース, 取付脚, プラグ, カップリングガード) | Mỗi cấu kiện có test kích thước và số mặt |
| 3 | Chạy tự động cả dòng SJ, xuất báo cáo đạt và gắn cờ | Tỷ lệ gắn cờ đủ thấp để xem tay được |
| 4 | Lặp lại theo dòng, xếp theo số mã; thêm 送風機, 給水ユニット khi có bản vẽ | Như giai đoạn 3 |
| 5 | Bài toán B | Định sau |

Không nhân rộng bất cứ thứ gì trước khi giai đoạn 1 qua được Rebro.

## Rủi ro chưa kiểm chứng

- Chưa ai xác nhận IFC tự ghi ra được Rebro nhận 接続口. Cần lấy một file `BSJ_MEP_*` do Rebro xuất làm mẫu để bắt chước cấu trúc.
- Chưa kiểm chứng việc tách bộ phận từ nét vẽ DXF chạy ổn định, nhất là với DXF kiểu cũ một layer.
- Tỷ lệ 1:1 mm của DXF mới suy ra từ một mẫu.
- Thứ tự dòng máy sau SJ phải xét lại khi Drive đủ file.
- Điều khoản của テラル về dùng lại bản vẽ chưa đọc được. Thư viện hiện chỉ dùng nội bộ; cần đọc điều khoản trước khi chia sẻ ra ngoài.
- Nên gom mã theo số bản vẽ trước khi xử lý, vì nhiều mã có thể dùng chung một bản vẽ. Chưa đo được mức trùng.
