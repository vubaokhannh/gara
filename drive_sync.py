# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.parse
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


CACHE_TTL_SECONDS = 30
_cache: dict = {}
_cache_lock = threading.Lock()


def _call_apps_script(webhook_url: str, params: dict, retries: int = 2) -> dict:
    """
    Gửi request tới Google Apps Script Web App (GET + query string để tránh mất body khi 302).
    Mọi thao tác đều an toàn khi gọi lại (thêm có ID chống trùng, sửa/xóa theo ID),
    nên tự thử lại tối đa `retries` lần khi lỗi mạng / quá thời gian.
    """
    query_str = urllib.parse.urlencode(params)
    sep = "&" if "?" in webhook_url else "?"
    full_url = f"{webhook_url}{sep}{query_str}"

    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(full_url, method="GET")
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
    raise DriveError(f"Không kết nối được Google Drive: {last_err}")


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


def drive_fetch_month(month_key: str, use_cache: bool = True) -> dict:
    """Đọc toàn bộ dữ liệu 1 tháng từ Google Sheet (có cache ngắn 30 giây)."""
    now = time.time()
    if use_cache:
        with _cache_lock:
            hit = _cache.get(month_key)
            if hit and now - hit[0] < CACHE_TTL_SECONDS:
                return hit[1]

    data = _call_apps_script(_require_url(), {"action": "list", "month_key": month_key})
    if not data.get("success"):
        raise DriveError(data.get("error", "Google Drive trả về lỗi"))
    records = data.get("records") or []
    if records and "id" not in records[0]:
        raise DriveError(OUTDATED_SCRIPT_MSG)
    _remember_links(month_key, data)
    with _cache_lock:
        _cache[month_key] = (now, data)
    return data


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
    }


def drive_append(month_key: str, rec_id: str, record: dict) -> dict:
    """Thêm bản ghi (cùng rec_id gửi lại nhiều lần vẫn chỉ ghi 1 dòng)."""
    params = {"action": "append", "month_key": month_key, "id": rec_id, **_record_params(record)}
    try:
        data = _call_apps_script(_require_url(), params)
    finally:
        _invalidate(month_key)
    if not data.get("success"):
        raise DriveError(data.get("error", "Google Drive từ chối ghi dữ liệu"))
    if "id" not in data:
        raise DriveError(OUTDATED_SCRIPT_MSG)
    _remember_links(month_key, data)
    return data


def drive_update(month_key: str, rec_id: str, record: dict) -> bool:
    """Sửa bản ghi theo ID. Trả về False nếu không tìm thấy."""
    params = {"action": "update", "month_key": month_key, "id": rec_id, **_record_params(record)}
    try:
        data = _call_apps_script(_require_url(), params)
    finally:
        _invalidate(month_key)
    if data.get("success"):
        return True
    if data.get("not_found"):
        return False
    raise DriveError(data.get("error", "Google Drive từ chối cập nhật"))


def drive_delete(month_key: str, rec_id: str) -> bool:
    """Xóa bản ghi theo ID. Trả về False nếu không tìm thấy."""
    try:
        data = _call_apps_script(_require_url(), {"action": "delete", "month_key": month_key, "id": rec_id})
    finally:
        _invalidate(month_key)
    if data.get("success"):
        return True
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
