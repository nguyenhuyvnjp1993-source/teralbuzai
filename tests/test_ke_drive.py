import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import ke_drive as kd  # noqa: E402


def test_tach_ten_co_ban():
    t = kd.tach_ten("テラル-陸上ポンプ-0972_SM50-2-51.5-e.zip")
    assert t == {"loai": "陸上ポンプ", "so_thu_tu": "0972", "ma_may": "SM50-2-51.5-e", "dong_may": "SM"}


def test_dong_may_bo_tien_to_co():
    assert kd.tach_ten("テラル-陸上ポンプ-0100_80MSP-8-518H-e.zip")["dong_may"] == "MSP"
    assert kd.tach_ten("テラル-陸上ポンプ-0101_8X6MKHS-5S-545-e.zip")["dong_may"] == "MKHS"
    assert kd.tach_ten("テラル-陸上ポンプ-0102_40LPS-e3755D.zip")["dong_may"] == "LPS"
    assert kd.tach_ten("テラル-陸上ポンプ-0103_LS-100X80A-e.zip")["dong_may"] == "LS"
    assert kd.tach_ten("テラル-陸上ポンプ-0104_SLP2-80-51.5-e.zip")["dong_may"] == "SLP"


def test_lech_mau():
    assert kd.tach_ten("SJ40-5.75.zip") is None
    assert kd.tach_ten("テラル-陸上ポンプ-0104_SJ.pdf") is None


def test_ghi_chu_ma():
    assert kd.ghi_chu_ma("SJ40-5.75-e") == []
    assert kd.ghi_chu_ma("LP25A5.08") == ["khong_hau_to_e"]
    assert kd.ghi_chu_ma("40LPS-e3755D") == ["e_giua_ma"]


def test_lap_bang_bo_trung_id_va_gan_co(tmp_path):
    files = [
        {"title": "テラル-陸上ポンプ-0001_SJ40-5.75-e.zip", "fileSize": "10", "id": "a"},
        {"title": "テラル-陸上ポンプ-0001_SJ40-5.75-e.zip", "fileSize": "10", "id": "a"},
        {"title": "テラル-陸上ポンプ-0002_SJ40-5.75-e.zip", "fileSize": "12", "id": "b"},
        {"name": "readme.txt", "size": "3", "id": "c"},
        {"title": "sub", "id": "d", "mimeType": "application/vnd.google-apps.folder"},
    ]
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"files": files}), encoding="utf-8")
    dongs, bo = kd.lap_bang(kd.doc_json(p))
    assert bo == 1
    assert len(dongs) == 3
    by_id = {d.drive_id: d for d in dongs}
    assert "ma_trung" in by_id["a"].ghi_chu and "ma_trung" in by_id["b"].ghi_chu
    assert "lech_mau" in by_id["c"].ghi_chu


def test_main_kiem_so_mong_doi(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"files": [
        {"title": "テラル-陸上ポンプ-0001_SJ40-5.75-e.zip", "fileSize": "10", "id": "a"}]}), encoding="utf-8")
    args = ["--json", str(p), "--csv", str(tmp_path / "o.csv"), "--bao-cao", str(tmp_path / "o.md")]
    assert kd.main(args + ["--so-mong-doi", "1"]) == 0
    assert kd.main(args + ["--so-mong-doi", "2"]) == 1


def test_doc_thu_muc(tmp_path):
    (tmp_path / "テラル-陸上ポンプ-0001_SJ40-5.75-e.zip").write_bytes(b"xx")
    dongs, _ = kd.lap_bang(kd.doc_thu_muc(tmp_path))
    assert dongs[0].ma_may == "SJ40-5.75-e" and dongs[0].kich_thuoc == 2
