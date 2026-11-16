# -*- coding: utf-8 -*-
import faulthandler
import io
import os
import socket
import sys
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file, g
from parser import parse_voice_text, validate_record, format_price_vn
from excel_manager import (
    ensure_excel_file,
    get_month_key_from_date,
    build_xlsx_bytes,
)
from drive_sync import (
    verify_pin,
    set_drive_webhook_url,
    get_saved_drive_links,
)
import storage
from storage import StorageError

app = Flask(__name__)


# ---- Theo dõi yêu cầu chậm / bị kẹt: ghi vào Logs của Render để biết chính xác kẹt ở đâu ----
_inflight: dict = {}
_inflight_lock = threading.Lock()


@app.before_request
def _track_start():
    g._req_key = object()
    g._req_t0 = time.time()
    with _inflight_lock:
        _inflight[g._req_key] = (g._req_t0, request.method, request.path)


@app.teardown_request
def _track_end(exc):
    key = getattr(g, "_req_key", None)
    if key is None:
        return
    with _inflight_lock:
        _inflight.pop(key, None)
    elapsed = time.time() - getattr(g, "_req_t0", time.time())
    if elapsed > 8:
        print(f"[SLOW] {request.method} {request.path} mất {elapsed:.1f}s", file=sys.stderr, flush=True)


def _watchdog() -> None:
    last_dump = 0.0
    while True:
        time.sleep(15)
        now = time.time()
        with _inflight_lock:
            stuck = [(round(now - t0), m, path) for (t0, m, path) in _inflight.values() if now - t0 > 45]
        if stuck and now - last_dump > 120:
            last_dump = now
            print(f"[WATCHDOG] yêu cầu đang chạy quá 45 giây (giây, phương thức, đường dẫn): {stuck}", file=sys.stderr, flush=True)
            faulthandler.dump_traceback(file=sys.stderr, all_threads=True)


if os.environ.get("GARA_WATCHDOG", "1") == "1":
    threading.Thread(target=_watchdog, daemon=True).start()


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


def _storage_error(err: StorageError, message: str = ""):
    text = message or "Không lưu được lên Google Drive."
    return (
        jsonify(
            {
                "success": False,
                "retryable": True,
                "errors": [f"{text} Dữ liệu vẫn giữ trên form, bấm Lưu để thử lại. ({err})"],
                "message": str(err),
            }
        ),
        502,
    )


@app.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint siêu nhẹ để Google Apps Script (hoặc Cron-job) ping định kỳ mỗi 10 phút,
    giúp giữ Server trên Render Free luôn thức 24/24 (không bị ngủ đông sau 15 phút).
    """
    return jsonify({"status": "ok", "service": "gara-voice"}), 200


@app.route("/")
def index():
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    lan_url = f"http://{local_ip}:{port}"
    return render_template(
        "index.html",
        lan_url=lan_url,
        current_filename=f"gara_{get_month_key_from_date()}.xlsx",
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
    saved_url = set_drive_webhook_url(payload.get("webhook_url", ""))
    return jsonify({"success": True, "configured": bool(saved_url), "drive_links": get_saved_drive_links(month_key)})


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """Nhận văn bản từ giọng nói, bóc tách thành các trường và kiểm tra hợp lệ."""
    payload = request.get_json(silent=True) or {}
    result = parse_voice_text(payload.get("text", ""))
    return jsonify(result)


@app.route("/api/save", methods=["POST"])
def api_save():
    """
    Kiểm tra PIN + tính hợp lệ rồi lưu.
    Chế độ Google Drive: ghi thẳng lên Google Sheet (nơi lưu duy nhất). Lỗi -> báo thất bại để thử lại.
    Gửi lại cùng `id` thì không bị ghi trùng.
    """
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "errors": ["Mã PIN không đúng hoặc chưa nhập mã PIN."]}), 401

    payload = request.get_json(silent=True) or {}
    client_id = payload.get("id", "")

    if payload.get("from_voice_direct") and payload.get("text"):
        parsed = parse_voice_text(payload["text"])
        if not parsed["is_valid"]:
            return jsonify({"success": False, "errors": parsed["errors"], "parsed": parsed}), 400
        payload = parsed

    is_valid, errors, cleaned = validate_record(payload)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        saved_row = storage.add_record(cleaned, client_id)
    except StorageError as e:
        return _storage_error(e)

    return jsonify(
        {
            "success": True,
            "message": f"Đã lưu vào {saved_row['filename']}!",
            "record": saved_row,
        }
    )


@app.route("/api/months", methods=["GET"])
def api_months():
    """Danh sách các tháng hiện có."""
    try:
        data = storage.get_records(request.args.get("month", ""))
    except StorageError as e:
        return jsonify({"success": False, "message": str(e)}), 502
    return jsonify({"months": data["months"], "current_month": get_month_key_from_date()})


@app.route("/api/records", methods=["GET"])
def api_records():
    """Lấy dữ liệu của tháng được chọn (cần đúng mã PIN)."""
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "message": "Vui lòng nhập mã PIN để truy cập."}), 401

    try:
        data = storage.get_records(request.args.get("month", ""))
    except StorageError as e:
        return jsonify({"success": False, "message": f"Không đọc được dữ liệu từ Google Drive: {e}"}), 502

    records = data["records"]
    total_revenue = sum(r.get("gia_int", 0) for r in records)

    return jsonify(
        {
            "month_key": data["month_key"],
            "filename": data["filename"],
            "months": data["months"],
            "records": records,
            "count": len(records),
            "total_revenue": format_price_vn(total_revenue) if total_revenue else "0",
            "drive": get_saved_drive_links(data["month_key"]),
            "stale": bool(data.get("stale")),
        }
    )


@app.route("/api/records/<rec_id>", methods=["PUT"])
def api_update_record(rec_id: str):
    """Sửa 1 bản ghi theo ID."""
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "errors": ["Vui lòng nhập đúng mã PIN để sửa dữ liệu."]}), 401

    payload = request.get_json(silent=True) or {}
    is_valid, errors, cleaned = validate_record(payload)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        updated = storage.update_record(request.args.get("month", ""), rec_id, cleaned)
    except StorageError as e:
        return _storage_error(e, "Không sửa được trên Google Drive.")
    if not updated:
        return jsonify({"success": False, "errors": ["Không tìm thấy dòng cần sửa (có thể đã bị xóa)."]}), 404
    return jsonify({"success": True, "message": "Đã cập nhật dòng dữ liệu.", "record": updated})


@app.route("/api/records/<rec_id>", methods=["DELETE"])
def api_delete_record(rec_id: str):
    """Xóa 1 bản ghi theo ID."""
    if not _check_request_pin():
        return jsonify({"success": False, "require_pin": True, "message": "Vui lòng nhập đúng mã PIN để xóa dữ liệu."}), 401

    try:
        ok = storage.delete_record(request.args.get("month", ""), rec_id)
    except StorageError as e:
        return jsonify({"success": False, "message": f"Không xóa được trên Google Drive: {e}"}), 502
    if ok:
        # Chế độ Excel local dùng số dòng làm ID nên các ID phía sau bị dịch -> giao diện cần tải lại
        return jsonify({"success": True, "message": "Đã xóa dòng dữ liệu.", "reload": not storage.using_drive()})
    return jsonify({"success": False, "message": "Không tìm thấy dòng cần xóa."}), 404


@app.route("/api/download-excel", methods=["GET"])
def api_download_excel():
    """Tạo file Excel (.xlsx) của tháng được chọn từ dữ liệu hiện có và tải về (cần đúng mã PIN)."""
    if not _check_request_pin():
        return "Vui lòng nhập đúng mã PIN trên trang Web để tải file Excel.", 401

    try:
        data = storage.get_records(request.args.get("month", ""))
    except StorageError as e:
        return f"Không đọc được dữ liệu từ Google Drive: {e}", 502

    ordered = list(reversed(data["records"]))  # cũ nhất trước
    content = build_xlsx_bytes(ordered, data["month_key"])
    return send_file(
        io.BytesIO(content),
        as_attachment=True,
        download_name=data["filename"],
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _warm_cache_on_start() -> None:
    """Nạp sẵn dữ liệu tháng hiện tại từ Google Sheet để lần mở trang đầu tiên không phải chờ."""
    if os.environ.get("GARA_WARM_CACHE", "1") != "1" or not storage.using_drive():
        return
    from drive_sync import drive_warm
    threading.Thread(target=drive_warm, args=(get_month_key_from_date(),), daemon=True).start()


_warm_cache_on_start()


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 64)
    print("HỆ THỐNG NHẬP LIỆU GARA BẰNG GIỌNG NÓI")
    if storage.using_drive():
        print("Nơi lưu dữ liệu:           Google Drive (Google Sheet)")
    else:
        print(f"Nơi lưu dữ liệu:           Excel local ({ensure_excel_file()})")
    print(f"Truy cập trên Máy tính:   http://127.0.0.1:{port}")
    print(f"Truy cập trên Điện thoại: http://{local_ip}:{port}")
    print("Mã PIN mặc định:          1234 (Đổi bằng biến môi trường APP_PIN)")
    print("=" * 64)
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "1") == "1")
