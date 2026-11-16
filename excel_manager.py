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

# 10 cột chuẩn theo yêu cầu Gara Ô tô
HEADERS = [
    "STT",
    "Ngày",
    "Biển Số",
    "Hiệu Xe",
    "Dịch vụ",
    "Nội Dung",
    "Báo Giá Dịch Vụ",
    "Thanh Toán",
    "Người Thực Hiện",
    "Ghi Chú",
]

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
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    ws.row_dimensions[1].height = 28
    for col_idx, header_text in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = header_text
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # Độ rộng tối ưu cho 10 cột
    col_widths = [6, 14, 16, 18, 22, 32, 18, 18, 18, 24]
    for idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def _style_data_row(ws, row_idx: int) -> None:
    data_font = Font(name="Arial", size=11)
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    ws.row_dimensions[row_idx].height = 24
    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=row_idx, column=col_idx)
        cell.font = data_font
        cell.border = thin_border
        # 1: STT, 2: Ngày, 3: Biển Số, 5: Dịch vụ, 8: Thanh Toán -> Căn giữa
        if col_idx in (1, 2, 3, 5, 8):
            cell.alignment = Alignment(horizontal="center", vertical="center")
        # 7: Báo Giá Dịch Vụ -> Căn phải
        elif col_idx == 7:
            cell.alignment = Alignment(horizontal="right", vertical="center")
        # 4: Hiệu Xe, 6: Nội Dung, 9: Người Thực Hiện, 10: Ghi Chú -> Căn trái
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")


def ensure_excel_file(month_key: str = "") -> str:
    """
    Kiểm tra và khởi tạo file Excel cho tháng tương ứng nếu chưa tồn tại.
    Nếu file cũ có cấu trúc cột cũ thì tự động nâng cấp lên 10 cột chuẩn.
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
        needs_migration = (
            ws.max_column != len(HEADERS)
            or ws.cell(row=1, column=1).value != "STT"
            or ws.cell(row=1, column=len(HEADERS)).value != "Ghi Chú"
        )
        if needs_migration:
            # Đọc lại dữ liệu cũ để nâng cấp sang 10 cột
            old_rows = []
            for r in range(2, ws.max_row + 1):
                row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
                if any(row_vals):
                    old_rows.append(row_vals)

            # Xóa sạch và tạo lại với 10 cột chuẩn
            wb.remove(ws)
            ws = wb.create_sheet(title=f"Thang_{mk}")
            ws.append(HEADERS)
            _style_header_row(ws)

            for idx, rvals in enumerate(old_rows, start=1):
                # Map từ cấu trúc cũ sang 10 cột
                thoi_gian = str(rvals[0] or "") if len(rvals) > 0 else ""
                bien_so = str(rvals[1] or "") if len(rvals) > 1 else ""
                hieu_xe = str(rvals[2] or "") if len(rvals) > 2 else ""
                dich_vu_old = str(rvals[3] or "") if len(rvals) > 3 else ""
                gia_old = rvals[4] if len(rvals) > 4 else ""
                nguoi_pt = str(rvals[5] or "") if len(rvals) > 5 else ""

                gia_int = parse_price_input(gia_old)
                gia_fmt = format_price_vn(gia_int) if gia_int > 0 else ""

                dich_vu_grp = "Đồng Sơn TM" if "đồng sơn" in dich_vu_old.lower() or "sơn" in dich_vu_old.lower() else "Bảo Trì & Sửa Chữa"

                new_row = [
                    idx,
                    thoi_gian,
                    bien_so,
                    hieu_xe,
                    dich_vu_grp,
                    dich_vu_old,
                    gia_fmt,
                    "Chưa Thanh Toán",
                    nguoi_pt,
                    "",
                ]
                ws.append(new_row)
                _style_data_row(ws, ws.max_row)

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


def append_to_excel(record: dict) -> dict:
    """
    Ghi nối tiếp 1 bản ghi vào file Excel của tháng tương ứng với đúng 10 cột chuẩn.
    Tự động tính STT tăng dần.
    """
    with _excel_lock:
        ngay = (record.get("ngay") or record.get("thoi_gian") or datetime.now().strftime("%d/%m/%Y")).strip()
        month_key = get_month_key_from_date(ngay)
        file_path = ensure_excel_file(month_key)

        wb = load_workbook(file_path)
        ws = wb.active

        stt = max(1, ws.max_row)  # Khi chỉ có header (max_row = 1) -> stt = 1
        bien_so = (record.get("bien_so") or "").strip().upper()
        hieu_xe = (record.get("hieu_xe") or record.get("hang_xe") or "").strip()
        dich_vu = (record.get("dich_vu") or "Bảo Trì & Sửa Chữa").strip()
        noi_dung = (record.get("noi_dung") or "").strip()
        bao_gia_int = parse_price_input(record.get("bao_gia") if "bao_gia" in record else record.get("gia"))
        bao_gia_formatted = format_price_vn(bao_gia_int) if bao_gia_int > 0 else ""
        thanh_toan = (record.get("thanh_toan") or "Chưa Thanh Toán").strip()
        nguoi_thuc_hien = (record.get("nguoi_thuc_hien") or record.get("nguoi_phu_trach") or "").strip()
        ghi_chu = (record.get("ghi_chu") or "").strip()

        row_values = [
            stt,
            ngay,
            bien_so,
            hieu_xe,
            dich_vu,
            noi_dung,
            bao_gia_formatted,
            thanh_toan,
            nguoi_thuc_hien,
            ghi_chu,
        ]

        ws.append(row_values)
        new_row_idx = ws.max_row
        _style_data_row(ws, new_row_idx)
        wb.save(file_path)

        return {
            "row_id": new_row_idx,
            "stt": stt,
            "month_key": month_key,
            "filename": os.path.basename(file_path),
            "ngay": ngay,
            "bien_so": bien_so,
            "hieu_xe": hieu_xe,
            "dich_vu": dich_vu,
            "noi_dung": noi_dung,
            "bao_gia": bao_gia_formatted,
            "bao_gia_int": bao_gia_int,
            "thanh_toan": thanh_toan,
            "nguoi_thuc_hien": nguoi_thuc_hien,
            "ghi_chu": ghi_chu,
            # Tương thích ngược:
            "thoi_gian": ngay,
            "hang_xe": hieu_xe,
            "gia": bao_gia_formatted,
            "gia_int": bao_gia_int,
            "nguoi_phu_trach": nguoi_thuc_hien,
        }


def read_all_records(month_key: str = "") -> tuple[str, str, list[dict]]:
    """
    Đọc tất cả các bản ghi của tháng tương ứng thành danh sách dict 10 trường.
    """
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = ensure_excel_file(mk)
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active

        records = []
        for row_idx in range(2, ws.max_row + 1):
            stt_val = ws.cell(row=row_idx, column=1).value
            ngay = ws.cell(row=row_idx, column=2).value
            bien_so = ws.cell(row=row_idx, column=3).value
            hieu_xe = ws.cell(row=row_idx, column=4).value
            dich_vu = ws.cell(row=row_idx, column=5).value
            noi_dung = ws.cell(row=row_idx, column=6).value
            bao_gia_val = ws.cell(row=row_idx, column=7).value
            thanh_toan = ws.cell(row=row_idx, column=8).value
            nguoi_thuc_hien = ws.cell(row=row_idx, column=9).value
            ghi_chu = ws.cell(row=row_idx, column=10).value

            if not any([ngay, bien_so, hieu_xe, dich_vu, noi_dung, bao_gia_val, nguoi_thuc_hien]):
                continue

            bao_gia_int = parse_price_input(bao_gia_val)
            bao_gia_str = format_price_vn(bao_gia_int) if bao_gia_int > 0 else str(bao_gia_val or "")

            records.append(
                {
                    "row_id": row_idx,
                    "stt": stt_val if stt_val is not None else (row_idx - 1),
                    "month_key": mk,
                    "ngay": str(ngay or ""),
                    "bien_so": str(bien_so or ""),
                    "hieu_xe": str(hieu_xe or ""),
                    "dich_vu": str(dich_vu or ""),
                    "noi_dung": str(noi_dung or ""),
                    "bao_gia": bao_gia_str,
                    "bao_gia_int": bao_gia_int,
                    "thanh_toan": str(thanh_toan or "Chưa Thanh Toán"),
                    "nguoi_thuc_hien": str(nguoi_thuc_hien or ""),
                    "ghi_chu": str(ghi_chu or ""),
                    # Tương thích ngược:
                    "thoi_gian": str(ngay or ""),
                    "hang_xe": str(hieu_xe or ""),
                    "gia": bao_gia_str,
                    "gia_int": bao_gia_int,
                    "nguoi_phu_trach": str(nguoi_thuc_hien or ""),
                }
            )

        records.reverse()
        return mk, os.path.basename(file_path), records


def delete_record_by_row(row_id: int, month_key: str = "") -> bool:
    """Xóa 1 dòng và tự động cập nhật lại STT từ 1..N"""
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = ensure_excel_file(mk)
        wb = load_workbook(file_path)
        ws = wb.active
        if 2 <= row_id <= ws.max_row:
            ws.delete_rows(row_id, 1)
            # Tái lập số thứ tự STT chuẩn
            for r in range(2, ws.max_row + 1):
                ws.cell(row=r, column=1).value = r - 1
            wb.save(file_path)
            return True
        return False


def update_record_by_row(row_id: int, record: dict, month_key: str = "") -> dict | None:
    """Sửa 1 dòng (giữ nguyên STT). Trả về bản ghi đã cập nhật hoặc None nếu không có dòng."""
    with _excel_lock:
        mk = get_month_key_from_date(month_key)
        file_path = ensure_excel_file(mk)
        wb = load_workbook(file_path)
        ws = wb.active
        if not (2 <= row_id <= ws.max_row):
            return None

        bao_gia_int = parse_price_input(record.get("bao_gia"))
        bao_gia_fmt = format_price_vn(bao_gia_int) if bao_gia_int > 0 else ""
        values = [
            record.get("ngay", ""),
            record.get("bien_so", ""),
            record.get("hieu_xe", ""),
            record.get("dich_vu", "Bảo Trì & Sửa Chữa"),
            record.get("noi_dung", ""),
            bao_gia_fmt,
            record.get("thanh_toan", "Chưa Thanh Toán"),
            record.get("nguoi_thuc_hien", ""),
            record.get("ghi_chu", ""),
        ]
        for offset, val in enumerate(values):
            ws.cell(row=row_id, column=2 + offset).value = val
        wb.save(file_path)
        return {**record, "row_id": row_id, "month_key": mk, "bao_gia": bao_gia_fmt}


def build_xlsx_bytes(records: list, month_key: str = "") -> bytes:
    """Tạo file .xlsx trong bộ nhớ từ danh sách bản ghi (cũ nhất trước). Không ghi ra đĩa."""
    from io import BytesIO

    mk = get_month_key_from_date(month_key)
    wb = Workbook()
    ws = wb.active
    ws.title = f"Thang_{mk}"
    ws.append(HEADERS)
    _style_header_row(ws)
    for idx, rec in enumerate(records, start=1):
        ws.append(
            [
                rec.get("stt") or idx,
                rec.get("ngay", ""),
                rec.get("bien_so", ""),
                rec.get("hieu_xe", ""),
                rec.get("dich_vu", ""),
                rec.get("noi_dung", ""),
                rec.get("bao_gia", ""),
                rec.get("thanh_toan", ""),
                rec.get("nguoi_thuc_hien", ""),
                rec.get("ghi_chu", ""),
            ]
        )
        _style_data_row(ws, ws.max_row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
