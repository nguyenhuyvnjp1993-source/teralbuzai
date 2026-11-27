# Cài đặt trên máy

Lô dựng đầy đủ chạy trên máy của bạn, đọc bản vẽ đã đồng bộ từ Google Drive và ghi IFC ra ổ cứng. Cần ba thứ: Python, `ezdxf`, `ifcopenshell`.

## 1. Python

Cài Python 3.11 trở lên.

- Windows: tải từ https://www.python.org/downloads/ , khi cài nhớ tích **Add python.exe to PATH**. Mở lại PowerShell rồi kiểm tra `py --version`.
- macOS: `brew install python@3.12`, hoặc bộ cài từ python.org. Kiểm tra `python3 --version`.

## 2. Lấy repo và tạo môi trường riêng

```powershell
git clone https://github.com/nguyenhuyvnjp1993-source/teralbuzai.git
cd teralbuzai
py -m venv .venv
.venv\Scripts\activate
```

Trên macOS thay hai dòng cuối bằng `python3 -m venv .venv` và `source .venv/bin/activate`.

## 3. Cài thư viện

```bash
pip install -r requirements.txt
```

`requirements.txt` gồm `ezdxf` (đọc DXF), `ifcopenshell` (ghi IFC) và `pytest` (chạy kiểm thử). `ifcopenshell` có bản dựng sẵn trên pip (đã thử cài được `ezdxf` 1.4.5 và `ifcopenshell` 0.9.0 trên Python 3.13, ngày 2026-11-27). Nếu pip báo không tìm thấy bản phù hợp với Python của bạn, hãy dùng Python 3.12 hoặc 3.13.

Kiểm tra:

```bash
python -c "import ezdxf, ifcopenshell; print(ezdxf.__version__, ifcopenshell.version)"
python -m pytest -q
```

## 4. Bản vẽ gốc

Cài Google Drive for desktop, đăng nhập, rồi đặt thư mục `テラル` ở chế độ **Available offline** (Mirror hoặc "Có sẵn ngoại tuyến") để script đọc được file mà không phải tải từng cái. Đường dẫn thường gặp:

- Windows: `G:\My Drive\テラル`
- macOS: `~/Library/CloudStorage/GoogleDrive-<tài khoản>/My Drive/テラル`

Bản vẽ không bao giờ được chép vào thư mục repo; `.gitignore` đã chặn `*.zip`, `*.dxf`, `*.pdf`, `*.ifc`.
