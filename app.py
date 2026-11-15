# -*- coding: utf-8 -*-
import os
import socket
from flask import Flask, render_template, request, jsonify, send_file
from parser import parse_voice_text, validate_record, format_price_vn
from excel_manager import (
    ensure_excel_file,
    append_to_excel,
    read_all_records,
    delete_record_by_row,
    list_monthly_files,
    get_month_key_from_date,
    replace_month_records_from_drive,
)
from drive_sync import (
    verify_pin,
    get_drive_webhook_url,
    set_drive_webhook_url,
    sync_append_to_drive,
    sync_delete_from_drive,
    fetch_month_from_drive,
    get_saved_drive_links,
)

app = Flask(__name__)


def get_local_ip() -> str:
    """Lấy địa chỉ IP mạng LAN của máy tính để điện thoại kết nối vào."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _check_request_pin() -> bool:
    pin = request.headers.get("X-App-Pin") or (request.get_json(silent=True) or {}).get("pin") or request.args.get("pin")
    return verify_pin(pin)


@app.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint siêu nhẹ để Google Apps Script (hoặc Cron-job) ping định kỳ mỗi 10 phút,
    giúp giữ Server trên Render Free luôn thức 24/24 (không bị ngủ đông sau 15 phút).
    """
    return jsonify({"status": "ok", "service": "gara-voice"}), 200


@app.route("/")
def index():
    current_month_file = ensure_excel_file()
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    lan_url = f"http://{local_ip}:{port}"
    return render_template(
        "index.html",
        lan_url=lan_url,
        current_filename=os.path.basename(current_month_file),
    )


@app.route("/api/verify-pin", methods=["POST"])
def api_verify_pin():
    payload = request.get_json(silent=True) or {}
    pin = payload.get("pin", "")
    if verify_pin(pin):
        return jsonify({"valid": True})
    return jsonify({"valid": False, "message": "Mã PIN không đúng."}), 401


@app.route("/api/drive-config", methods=["GET", "POST"])
def api_drive_config():
    month_key = get_month_key_from_date(request.args.get("month", ""))
    if request.method == "GET":
        return jsonify(get_saved_drive_links(month_key))

    if not _check_request_pin():
        return jsonify({"success": False, "errors": ["Vui lòng nhập đúng mã PIN để cấu hình Google Drive."]}), 401

    payload = request.get_json(silent=True) or {}
    webhook_url = payload.get("webhook_url", "")
    saved_url = set_drive_webhook_url(webhook_url)

    # Thử đồng bộ ngay tháng hiện tại nếu vừa dán link mới
    drive_info = {}
    if saved_url:
        drive_info = fetch_month_from_drive(month_key)
        if drive_info.get("success") and drive_info.get("records"):
            replace_month_records_from_drive(month_key, drive_info["records"])

    return jsonify(
        {
            "success": True,
            "configured": bool(saved_url),
            "drive_links": get_saved_drive_links(month_key),
            "drive_pull": bool(drive_info.get("success")),
        }
    )


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """
    Nhận văn bản từ giọng nói (Web Speech API hoặc bàn phím giọng nói điện thoại),
    bóc tách thành 5 trường và kiểm tra hợp lệ.
    """
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    result = parse_voice_text(text)
    return jsonify(result)


@app.route("/api/save", methods=["POST"])
def api_save():
    """
    Kiểm tra mã PIN + tính hợp lệ, sau đó:
      1. Ghi vào file Excel của tháng tương ứng (gara_MM_YYYY.xlsx)
      2. Tự động đồng bộ sang Google Drive (tự tạo file tháng trên Drive nếu chưa có)
    """
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "errors": ["Mã PIN không đúng hoặc chưa nhập mã PIN."]}), 401

    payload = request.get_json(silent=True) or {}

    if payload.get("from_voice_direct") and payload.get("text"):
        parsed = parse_voice_text(payload["text"])
        if not parsed["is_valid"]:
            return jsonify({"success": False, "errors": parsed["errors"], "parsed": parsed}), 400
        payload = parsed

    is_valid, errors, cleaned = validate_record(payload)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    # 1. Lưu vào file .xlsx trên Server
    saved_row = append_to_excel(cleaned)

    # 2. Đồng bộ tự động lên Google Drive theo tháng
    drive_result = sync_append_to_drive(saved_row["month_key"], saved_row)

    return jsonify(
        {
            "success": True,
            "message": f"Đã lưu vào {saved_row['filename']}!",
            "record": saved_row,
            "drive": drive_result,
        }
    )


@app.route("/api/months", methods=["GET"])
def api_months():
    """Lấy danh sách các file Excel theo từng tháng hiện có."""
    months = list_monthly_files()
    current_mk = get_month_key_from_date()
    return jsonify({"months": months, "current_month": current_mk})


@app.route("/api/records", methods=["GET"])
def api_records():
    """
    Lấy danh sách dữ liệu của tháng được chọn (Yêu cầu đúng mã PIN).
    Nếu file local đang trống (do Cloud Server mới khởi động lại) và đã nối Google Drive,
    tự động kéo dữ liệu của tháng đó từ Google Drive về file .xlsx!
    """
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "message": "Vui lòng nhập mã PIN để truy cập."}), 401

    month_param = request.args.get("month", "")
    force_sync = request.args.get("sync_drive", "") == "1"
    month_key, filename, records = read_all_records(month_param)

    if (len(records) == 0 or force_sync) and get_drive_webhook_url():
        drive_data = fetch_month_from_drive(month_key)
        if drive_data.get("success") and isinstance(drive_data.get("records"), list):
            if len(drive_data["records"]) > 0 or force_sync:
                replace_month_records_from_drive(month_key, drive_data["records"])
                month_key, filename, records = read_all_records(month_key)

    total_revenue = sum(r.get("gia_int", 0) for r in records)
    months = list_monthly_files()
    drive_links = get_saved_drive_links(month_key)

    return jsonify(
        {
            "month_key": month_key,
            "filename": filename,
            "months": months,
            "records": records,
            "count": len(records),
            "total_revenue": format_price_vn(total_revenue) if total_revenue else "0",
            "drive": drive_links,
        }
    )


@app.route("/api/records/<int:row_id>", methods=["DELETE"])
def api_delete_record(row_id: int):
    """Xóa 1 dòng trong file Excel của tháng tương ứng và đồng bộ xóa trên Google Drive."""
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "message": "Vui lòng nhập đúng mã PIN để xóa dữ liệu."}), 401

    month_param = request.args.get("month", "")
    mk = get_month_key_from_date(month_param)
    ok = delete_record_by_row(row_id, mk)
    if ok:
        sync_delete_from_drive(mk, row_id)
        return jsonify({"success": True, "message": "Đã xóa dòng dữ liệu."})
    return jsonify({"success": False, "message": "Không tìm thấy dòng cần xóa."}), 404


@app.route("/api/download-excel", methods=["GET"])
def api_download_excel():
    """Tải trực tiếp file Excel (.xlsx) của tháng được chọn (Yêu cầu đúng mã PIN)."""
    if not _check_request_pin():
        return "Vui lòng nhập đúng mã PIN trên trang Web để tải file Excel.", 401

    month_param = request.args.get("month", "")
    file_path = ensure_excel_file(month_param)
    filename = os.path.basename(file_path)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    current_file = ensure_excel_file()
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 64)
    print("🚗 HỆ THỐNG NHẬP LIỆU GARA BẰNG GIỌNG NÓI (PUBLIC & GOOGLE DRIVE)")
    print(f"📂 File Excel tháng hiện tại: {current_file}")
    print(f"💻 Truy cập trên Máy tính:   http://127.0.0.1:{port}")
    print(f"📱 Truy cập trên Điện thoại: http://{local_ip}:{port}")
    print("🔑 Mã PIN mặc định:          1234 (Đổi bằng biến môi trường APP_PIN)")
    print("=" * 64)
    app.run(host="0.0.0.0", port=port, debug=True)
