# -*- coding: utf-8 -*-
import os
import json
import requests
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


def _load_local_config() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_local_config(cfg: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_drive_webhook_url() -> str:
    """
    Lấy URL Webhook của Google Apps Script (ưu tiên config.json nếu có, sau đó tới biến môi trường).
    """
    cfg = _load_local_config()
    local_url = (cfg.get("drive_webhook_url") or "").strip()
    if local_url:
        return local_url
    return os.environ.get("DRIVE_WEBHOOK_URL", "").strip()


def set_drive_webhook_url(url: str) -> str:
    """Lưu URL Webhook của Google Apps Script vào config.json."""
    cfg = _load_local_config()
    cleaned = (url or "").strip()
    cfg["drive_webhook_url"] = cleaned
    _save_local_config(cfg)
    return cleaned


def get_app_pin() -> str:
    """
    Lấy mã PIN bảo mật (mặc định là '1234' hoặc từ biến môi trường APP_PIN).
    """
    env_pin = os.environ.get("APP_PIN", "").strip()
    if env_pin:
        return env_pin
    cfg = _load_local_config()
    return (cfg.get("app_pin") or "1234").strip()


def verify_pin(input_pin: str) -> bool:
    expected = get_app_pin()
    if not expected:
        return True
    return str(input_pin or "").strip() == expected


class DriveError(Exception):
    """Lỗi khi làm việc với Google Drive / Apps Script."""


OUTDATED_SCRIPT_MSG = (
    "Google Apps Script đang là bản cũ (chưa có mã ID cho từng dòng). "
    "Hãy dán lại file google_apps_script.gs và Deploy phiên bản mới."
)


# Dùng lại kết nối TLS tới Google giữa các lần gọi (tiết kiệm ~0.3-0.6s mỗi lần)
_session = requests.Session()

CACHE_TTL_SECONDS = 30
MAX_STALE_SECONDS = 600
_refreshing: set = set()
MONTHS_TTL_SECONDS = 600
_months_cache: dict = {}
_cache: dict = {}
_cache_lock = threading.Lock()


def _call_apps_script(webhook_url: str, params: dict, retries: int = 1) -> dict:
    """
    Gửi request tới Google Apps Script Web App (GET + query string để tránh mất body khi 302).
    Mọi thao tác đều an toàn khi gọi lại (thêm có ID chống trùng, sửa/xóa theo ID),
    nên tự thử lại tối đa `retries` lần khi lỗi mạng / quá thời gian.
    """
    last_err = ""
    for attempt in range(retries + 1):
        try:
            resp = _session.get(webhook_url, params=params, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_err = _describe_error(e)
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
    raise DriveError(f"Không kết nối được Google Drive: {last_err}")


def _describe_error(e: Exception) -> str:
    """Mô tả lỗi bằng tiếng Việt, KHÔNG kèm link Apps Script (link là bí mật: ai có link cũng sửa được dữ liệu)."""
    if isinstance(e, requests.exceptions.Timeout):
        return "Google trả lời quá chậm (quá 20 giây), thử lại sau ít giây."
    if isinstance(e, requests.exceptions.HTTPError):
        code = e.response.status_code if e.response is not None else "?"
        if code in (401, 403):
            return f"Google từ chối truy cập (HTTP {code}) - kiểm tra Apps Script đang để 'Ai có quyền truy cập' là 'Bất kỳ ai'."
        if code == 404:
            return "Không tìm thấy Apps Script (HTTP 404) - link DRIVE_WEBHOOK_URL có thể sai hoặc bản triển khai đã bị xóa."
        return f"Google trả về lỗi HTTP {code}."
    if isinstance(e, requests.exceptions.ConnectionError):
        return "Không kết nối được tới máy chủ Google (lỗi mạng)."
    if isinstance(e, ValueError):  # JSON không đọc được
        return ("Google trả về nội dung không đúng định dạng - thường do link Apps Script sai hoặc "
                "chưa cho phép 'Bất kỳ ai' truy cập (Google trả về trang đăng nhập).")
    return f"Lỗi không xác định ({type(e).__name__})."


def _remember_links(month_key: str, data: dict) -> None:
    if not (data.get("file_url") or data.get("folder_url")):
        return
    cfg = _load_local_config()
    if data.get("file_url"):
        file_urls = cfg.get("drive_file_urls") or {}
        file_urls[month_key] = data["file_url"]
        cfg["drive_file_urls"] = file_urls
    if data.get("folder_url"):
        cfg["drive_folder_url"] = data["folder_url"]
    _save_local_config(cfg)


def _require_url() -> str:
    url = get_drive_webhook_url()
    if not url:
        raise DriveError("Chưa cấu hình DRIVE_WEBHOOK_URL")
    return url


def _invalidate(month_key: str) -> None:
    with _cache_lock:
        _cache.pop(month_key, None)


def drive_configured() -> bool:
    return bool(get_drive_webhook_url())


def _fetch_and_store(month_key: str) -> dict:
    data = _call_apps_script(_require_url(), {"action": "list", "month_key": month_key})
    if not data.get("success"):
        raise DriveError(data.get("error", "Google Drive trả về lỗi"))
    records = data.get("records") or []
    if records and "id" not in records[0]:
        raise DriveError(OUTDATED_SCRIPT_MSG)
    _remember_links(month_key, data)
    with _cache_lock:
        _cache[month_key] = (time.time(), data)
    return data


def _refresh_in_background(month_key: str) -> None:
    with _cache_lock:
        if month_key in _refreshing:
            return
        _refreshing.add(month_key)

    def work():
        try:
            _fetch_and_store(month_key)
        except Exception:  # noqa: BLE001  - lỗi làm mới ngầm không ảnh hưởng người dùng
            pass
        finally:
            with _cache_lock:
                _refreshing.discard(month_key)

    threading.Thread(target=work, daemon=True).start()


def drive_fetch_month(month_key: str, use_cache: bool = True):
    """
    Đọc dữ liệu 1 tháng. Trả về (data, stale).
      - Cache còn mới (< 30s): trả ngay.
      - Cache cũ nhưng chưa quá 10 phút: trả NGAY bản cũ (stale=True) và làm mới ngầm.
      - Chưa có cache / quá cũ: phải chờ đọc từ Google Sheet.
    """
    if use_cache:
        with _cache_lock:
            hit = _cache.get(month_key)
        if hit:
            age = time.time() - hit[0]
            if age < CACHE_TTL_SECONDS:
                return _snapshot(hit[1]), False
            if age < MAX_STALE_SECONDS:
                _refresh_in_background(month_key)
                return _snapshot(hit[1]), True
    return _snapshot(_fetch_and_store(month_key)), False


def _snapshot(data: dict) -> dict:
    return {**data, "records": list(data.get("records") or [])}


def drive_warm(month_key: str) -> None:
    """Nạp sẵn cache (gọi lúc server vừa khởi động để lần mở trang đầu không phải chờ)."""
    try:
        _fetch_and_store(month_key)
    except Exception:  # noqa: BLE001
        pass


def drive_months() -> list:
    """Danh sách các tháng có trên Drive (cache 10 phút vì hiếm khi đổi)."""
    now = time.time()
    with _cache_lock:
        hit = _months_cache.get("m")
        if hit and now - hit[0] < MONTHS_TTL_SECONDS:
            return hit[1]
    data = _call_apps_script(_require_url(), {"action": "months"})
    if not data.get("success"):
        raise DriveError(data.get("error", "Google Drive trả về lỗi"))
    months = data.get("months", [])
    with _cache_lock:
        _months_cache["m"] = (now, months)
    return months


def _record_params(record: dict) -> dict:
    return {
        "ngay": record.get("ngay", ""),
        "bien_so": record.get("bien_so", ""),
        "hieu_xe": record.get("hieu_xe", ""),
        "dich_vu": record.get("dich_vu", ""),
        "noi_dung": record.get("noi_dung", ""),
        "bao_gia": str(record.get("bao_gia_hien_thi") or record.get("bao_gia") or ""),
        "thanh_toan": record.get("thanh_toan", ""),
        "nguoi_thuc_hien": record.get("nguoi_thuc_hien", ""),
        "ghi_chu": record.get("ghi_chu", ""),
        "so_dien_thoai": record.get("so_dien_thoai", ""),
        "ten_khach_hang": record.get("ten_khach_hang", ""),
    }


def _patch_cache(month_key: str, fn) -> None:
    """Sửa cache tại chỗ sau khi ghi thành công (copy-on-write để request khác đang đọc không bị ảnh hưởng)."""
    with _cache_lock:
        hit = _cache.get(month_key)
        if not hit:
            return
        new_records = fn(list(hit[1].get("records") or []))
        _cache[month_key] = (hit[0], {**hit[1], "records": new_records})


def drive_append(month_key: str, rec_id: str, record: dict) -> dict:
    """Thêm bản ghi (cùng rec_id gửi lại nhiều lần vẫn chỉ ghi 1 dòng)."""
    fields = _record_params(record)
    params = {"action": "append", "month_key": month_key, "id": rec_id, **fields}
    try:
        data = _call_apps_script(_require_url(), params)
    except Exception:
        _invalidate(month_key)
        raise
    if not data.get("success"):
        _invalidate(month_key)
        raise DriveError(data.get("error", "Google Drive từ chối ghi dữ liệu"))
    if "id" not in data:
        raise DriveError(OUTDATED_SCRIPT_MSG)
    _remember_links(month_key, data)

    if data.get("duplicate"):
        _invalidate(month_key)  # đã có sẵn trên Sheet -> đọc lại cho chắc
    else:
        row = {"id": rec_id, "stt": str(data.get("stt", "")), "month_key": month_key, **fields}
        _patch_cache(month_key, lambda recs: recs + [row] if not any(r.get("id") == rec_id for r in recs) else recs)
    with _cache_lock:
        known = {m.get("month_key") for m in (_months_cache.get("m") or (0, []))[1]}
        if month_key not in known:
            _months_cache.pop("m", None)
    return data


def drive_update(month_key: str, rec_id: str, record: dict) -> bool:
    """Sửa bản ghi theo ID. Trả về False nếu không tìm thấy."""
    fields = _record_params(record)
    params = {"action": "update", "month_key": month_key, "id": rec_id, **fields}
    try:
        data = _call_apps_script(_require_url(), params)
    except Exception:
        _invalidate(month_key)
        raise
    if data.get("success"):
        _patch_cache(month_key, lambda recs: [{**r, **fields} if r.get("id") == rec_id else r for r in recs])
        return True
    _invalidate(month_key)
    if data.get("not_found"):
        return False
    raise DriveError(data.get("error", "Google Drive từ chối cập nhật"))


def drive_delete(month_key: str, rec_id: str) -> bool:
    """Xóa bản ghi theo ID. Trả về False nếu không tìm thấy."""
    try:
        data = _call_apps_script(_require_url(), {"action": "delete", "month_key": month_key, "id": rec_id})
    except Exception:
        _invalidate(month_key)
        raise
    if data.get("success"):
        def remove(recs):
            kept = [r for r in recs if r.get("id") != rec_id]
            return [{**r, "stt": str(i)} for i, r in enumerate(kept, start=1)]  # Sheet đánh lại STT 1..N
        _patch_cache(month_key, remove)
        return True
    _invalidate(month_key)
    if data.get("not_found"):
        return False
    raise DriveError(data.get("error", "Google Drive từ chối xóa"))


def get_saved_drive_links(month_key: str) -> dict:
    cfg = _load_local_config()
    file_urls = cfg.get("drive_file_urls") or {}
    return {
        "configured": bool(get_drive_webhook_url()),
        "file_url": file_urls.get(month_key, ""),
        "folder_url": cfg.get("drive_folder_url", ""),
    }
