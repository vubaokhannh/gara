# -*- coding: utf-8 -*-
"""
Lớp lưu trữ dùng chung cho app:
  - Đã cấu hình Google Drive  -> Google Sheet là NƠI LƯU DUY NHẤT (server không giữ dữ liệu).
  - Chưa cấu hình Drive       -> dùng file Excel local (chế độ chạy thử trên máy).
Mỗi bản ghi có `id` duy nhất để sửa / xóa chính xác.
"""
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor

from parser import format_price_vn, parse_price_input
from excel_manager import (
    append_to_excel,
    read_all_records,
    delete_record_by_row,
    update_record_by_row,
    list_monthly_files,
    get_month_key_from_date,
)
from drive_sync import (
    DriveError,
    drive_configured,
    drive_fetch_month,
    drive_months,
    drive_append,
    drive_update,
    drive_delete,
)


class StorageError(Exception):
    pass


ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,40}$")


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def clean_id(value) -> str:
    v = str(value or "").strip()
    return v if ID_PATTERN.match(v) else ""


def using_drive() -> bool:
    return drive_configured()


def _shape(rec: dict, month_key: str) -> dict:
    """Chuẩn hóa 1 bản ghi từ Drive về cùng dạng với bản ghi local."""
    gia_int = parse_price_input(rec.get("bao_gia"))
    gia_str = format_price_vn(gia_int) if gia_int > 0 else str(rec.get("bao_gia") or "")
    out = {
        "id": str(rec.get("id") or ""),
        "stt": rec.get("stt", ""),
        "month_key": month_key,
        "ngay": rec.get("ngay", ""),
        "bien_so": rec.get("bien_so", ""),
        "hieu_xe": rec.get("hieu_xe", ""),
        "dich_vu": rec.get("dich_vu", ""),
        "noi_dung": rec.get("noi_dung", ""),
        "bao_gia": gia_str,
        "bao_gia_int": gia_int,
        "thanh_toan": rec.get("thanh_toan", ""),
        "nguoi_thuc_hien": rec.get("nguoi_thuc_hien", ""),
        "ghi_chu": rec.get("ghi_chu", ""),
    }
    out["gia_int"] = gia_int
    return out


def get_records(month_param: str = "") -> dict:
    """Trả về {month_key, filename, records (mới nhất trước), months}."""
    mk = get_month_key_from_date(month_param)
    if using_drive():
        # Lấy dữ liệu tháng và danh sách tháng SONG SONG (khi chưa có cache, đỡ phải chờ nối tiếp 2 lần)
        with ThreadPoolExecutor(max_workers=2) as pool:
            months_future = pool.submit(drive_months)
            try:
                data, stale = drive_fetch_month(mk)
            except DriveError as e:
                raise StorageError(str(e)) from e
            try:
                raw_months = months_future.result()
            except DriveError:
                raw_months = []  # danh sách tháng lỗi không được chặn việc xem dữ liệu
        records = [_shape(r, mk) for r in data.get("records", [])]
        records.reverse()
        months = [
            {"month_key": m["month_key"], "label": m["label"], "filename": m.get("filename", "")}
            for m in raw_months
        ]
        months.sort(key=lambda m: (m["month_key"][3:], m["month_key"][:2]), reverse=True)
        if mk not in {m["month_key"] for m in months}:
            months.insert(0, {"month_key": mk, "label": f"Tháng {mk[:2]}/{mk[3:]}", "filename": f"gara_{mk}.xlsx"})
        return {"month_key": mk, "filename": f"gara_{mk}.xlsx", "records": records, "months": months, "stale": stale}

    mk, filename, records = read_all_records(mk)
    for r in records:
        r["id"] = str(r["row_id"])
    return {"month_key": mk, "filename": filename, "records": records, "months": list_monthly_files()}


def add_record(cleaned: dict, rec_id: str = "") -> dict:
    rec_id = clean_id(rec_id) or new_id()
    mk = get_month_key_from_date(cleaned.get("ngay", ""))
    if using_drive():
        try:
            res = drive_append(mk, rec_id, cleaned)
        except DriveError as e:
            raise StorageError(str(e)) from e
        gia_int = parse_price_input(cleaned.get("bao_gia"))
        return {
            **cleaned,
            "id": rec_id,
            "stt": res.get("stt", ""),
            "month_key": mk,
            "filename": f"gara_{mk}.xlsx",
            "bao_gia": format_price_vn(gia_int) if gia_int > 0 else "",
            "bao_gia_int": gia_int,
            "duplicate": bool(res.get("duplicate")),
        }
    saved = append_to_excel(cleaned)
    saved["id"] = str(saved["row_id"])
    return saved


def update_record(month_param: str, rec_id: str, cleaned: dict):
    """Trả về bản ghi đã cập nhật, hoặc None nếu không tìm thấy."""
    mk = get_month_key_from_date(month_param)
    if using_drive():
        try:
            ok = drive_update(mk, rec_id, cleaned)
        except DriveError as e:
            raise StorageError(str(e)) from e
        if not ok:
            return None
        gia_int = parse_price_input(cleaned.get("bao_gia"))
        return {**cleaned, "id": rec_id, "month_key": mk, "bao_gia": format_price_vn(gia_int) if gia_int > 0 else ""}
    try:
        row_id = int(rec_id)
    except ValueError:
        return None
    updated = update_record_by_row(row_id, cleaned, mk)
    if updated:
        updated["id"] = str(row_id)
    return updated


def delete_record(month_param: str, rec_id: str) -> bool:
    mk = get_month_key_from_date(month_param)
    if using_drive():
        try:
            return drive_delete(mk, rec_id)
        except DriveError as e:
            raise StorageError(str(e)) from e
    try:
        return delete_record_by_row(int(rec_id), mk)
    except ValueError:
        return False
