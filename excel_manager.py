# -*- coding: utf-8 -*-
import os
import re
import threading
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from parser import format_price_vn, parse_price_input

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 6 cột: Thời gian | Biển số | Hãng xe | Dịch vụ | Giá | Người phụ trách
HEADERS = ["Thời gian", "Biển số", "Hãng xe", "Dịch vụ", "Giá", "Người phụ trách"]

_excel_lock = threading.Lock()


def get_month_key_from_date(date_str: str = "") -> str:
    """
    Trích xuất mã tháng dạng 'MM_YYYY' từ chuỗi ngày 'DD/MM/YYYY' hoặc 'YYYY-MM'.
    Nếu không truyền hoặc không hợp lệ thì lấy tháng hiện tại.
    """
    s = (date_str or "").strip()

    m_month_year = re.match(r"^(\d{1,2})[_/\-](\d{4})$", s)
    if m_month_year:
        mm = int(m_month_year.group(1))
        yyyy = int(m_month_year.group(2))
        if 1 <= mm <= 12:
            return f"{mm:02d}_{yyyy}"

    m_iso_month = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if m_iso_month:
        yyyy = int(m_iso_month.group(1))
        mm = int(m_iso_month.group(2))
        if 1 <= mm <= 12:
            return f"{mm:02d}_{yyyy}"

    m_full_date = re.match(r"^(\d{1,2})[_/\-](\d{1,2})[_/\-](\d{4})$", s)
    if m_full_date:
        mm = int(m_full_date.group(2))
        yyyy = int(m_full_date.group(3))
        if 1 <= mm <= 12:
            return f"{mm:02d}_{yyyy}"

    now = datetime.now()
    return now.strftime("%m_%Y")


def get_excel_path_for_month(month_key: str = "") -> str:
    mk = get_month_key_from_date(month_key)
    filename = f"gara_{mk}.xlsx"
    return os.path.join(DATA_DIR, filename)


def _style_header_row(ws) -> None:
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    ws.row_dimensions[1].height = 26
    for col_idx, header_text in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = header_text
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    col_widths = [16, 18, 18, 28, 16, 20]
    for idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def ensure_excel_file(month_key: str = "") -> str:
    """
    Kiểm tra và khởi tạo file Excel cho tháng tương ứng nếu chưa tồn tại.
    Nếu file cũ mới chỉ có 5 cột thì tự động bổ sung cột thứ 6 'Người phụ trách'.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    mk = get_month_key_from_date(month_key)
    file_path = get_excel_path_for_month(mk)

    if not os.path.exists(file_path):
        wb = Workbook()
        ws = wb.active
        ws.title = f"Thang_{mk}"
        ws.append(HEADERS)
        _style_header_row(ws)
        wb.save(file_path)
    else:
        wb = load_workbook(file_path)
        ws = wb.active
        if ws.max_column < len(HEADERS) or ws.cell(row=1, column=6).value != "Người phụ trách":
            _style_header_row(ws)
            wb.save(file_path)

    return file_path


def list_monthly_files() -> list[dict]:
    os.makedirs(DATA_DIR, exist_ok=True)
    current_mk = get_month_key_from_date()
    ensure_excel_file(current_mk)

    months_map = {}
    for fname in os.listdir(DATA_DIR):
        m = re.match(r"^gara_(\d{2})_(\d{4})\.xlsx$", fname)
        if m:
            mm, yyyy = m.group(1), m.group(2)
            mk = f"{mm}_{yyyy}"
            months_map[mk] = {
                "month_key": mk,
                "label": f"Tháng {mm}/{yyyy}",
                "filename": fname,
                "sort_key": (int(yyyy), int(mm)),
            }

    sorted_items = sorted(months_map.values(), key=lambda x: x["sort_key"], reverse=True)
    for item in sorted_items:
        item.pop("sort_key", None)
    return sorted_items


def _style_data_row(ws, row_idx: int) -> None:
    data_font = Font(name="Arial", size=11)
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    ws.row_dimensions[row_idx].height = 22
    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=row_idx, column=col_idx)
        cell.font = data_font
        cell.border = thin_border
        if col_idx in (1, 2):
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif col_idx == 5:
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")


def append_to_excel(record: dict) -> dict:
    """
    Ghi nối tiếp 1 bản ghi vào file Excel của tháng tương ứng.
    Cột Giá có thể để trống nếu không nhập.
    """
    with _excel_lock:
        thoi_gian = record.get("thoi_gian", "")
        month_key = get_month_key_from_date(thoi_gian)
        file_path = ensure_excel_file(month_key)

        wb = load_workbook(file_path)
        ws = wb.active

        gia_int = parse_price_input(record.get("gia", 0))
        gia_formatted = format_price_vn(gia_int) if gia_int > 0 else ""
        nguoi_phu_trach = (record.get("nguoi_phu_trach") or "").strip()

        row_values = [
            thoi_gian,
            record.get("bien_so", ""),
            record.get("hang_xe", ""),
            record.get("dich_vu", ""),
            gia_formatted,
            nguoi_phu_trach,
        ]

        ws.append(row_values)
        new_row_idx = ws.max_row
        _style_data_row(ws, new_row_idx)
        wb.save(file_path)

        return {
            "row_id": new_row_idx,
            "month_key": month_key,
            "filename": os.path.basename(file_path),
            "thoi_gian": row_values[0],
            "bien_so": row_values[1],
            "hang_xe": row_values[2],
            "dich_vu": row_values[3],
            "gia": gia_formatted,
            "gia_int": gia_int,
            "nguoi_phu_trach": nguoi_phu_trach,
        }


def read_all_records(month_key: str = "") -> tuple[str, str, list[dict]]:
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = ensure_excel_file(mk)
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active

        records = []
        for row_idx in range(2, ws.max_row + 1):
            thoi_gian = ws.cell(row=row_idx, column=1).value
            bien_so = ws.cell(row=row_idx, column=2).value
            hang_xe = ws.cell(row=row_idx, column=3).value
            dich_vu = ws.cell(row=row_idx, column=4).value
            gia_val = ws.cell(row=row_idx, column=5).value
            nguoi_phu_trach = ws.cell(row=row_idx, column=6).value

            if not any([thoi_gian, bien_so, hang_xe, dich_vu, gia_val, nguoi_phu_trach]):
                continue

            gia_int = parse_price_input(gia_val)
            gia_str = format_price_vn(gia_int) if gia_int > 0 else str(gia_val or "")

            records.append(
                {
                    "row_id": row_idx,
                    "month_key": mk,
                    "thoi_gian": str(thoi_gian or ""),
                    "bien_so": str(bien_so or ""),
                    "hang_xe": str(hang_xe or ""),
                    "dich_vu": str(dich_vu or ""),
                    "gia": gia_str,
                    "gia_int": gia_int,
                    "nguoi_phu_trach": str(nguoi_phu_trach or ""),
                }
            )

        records.reverse()
        return mk, os.path.basename(file_path), records


def delete_record_by_row(row_id: int, month_key: str = "") -> bool:
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = ensure_excel_file(mk)
        wb = load_workbook(file_path)
        ws = wb.active
        if 2 <= row_id <= ws.max_row:
            ws.delete_rows(row_id, 1)
            wb.save(file_path)
            return True
        return False


def replace_month_records_from_drive(month_key: str, drive_records: list[dict]) -> None:
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = get_excel_path_for_month(mk)
        if os.path.exists(file_path):
            os.remove(file_path)
        ensure_excel_file(mk)

        wb = load_workbook(file_path)
        ws = wb.active

        for rec in drive_records:
            gia_int = parse_price_input(rec.get("gia", 0))
            gia_formatted = format_price_vn(gia_int) if gia_int > 0 else ""
            ws.append(
                [
                    rec.get("thoi_gian", ""),
                    rec.get("bien_so", ""),
                    rec.get("hang_xe", ""),
                    rec.get("dich_vu", ""),
                    gia_formatted,
                    rec.get("nguoi_phu_trach", ""),
                ]
            )
            _style_data_row(ws, ws.max_row)

        wb.save(file_path)
