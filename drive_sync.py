# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.parse

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
    Lấy URL Webhook của Google Apps Script (ưu tiên biến môi trường, sau đó tới config.json).
    """
    env_url = os.environ.get("DRIVE_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url
    cfg = _load_local_config()
    return (cfg.get("drive_webhook_url") or "").strip()


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


def sync_append_to_drive(month_key: str, record: dict) -> dict:
    """
    Gửi bản ghi mới sang Google Drive (Apps Script) để tự động tạo/ghi vào file tháng tương ứng.
    """
    webhook_url = get_drive_webhook_url()
    if not webhook_url:
        return {"synced": False, "reason": "Chưa cấu hình DRIVE_WEBHOOK_URL"}

    payload = {
        "action": "append",
        "month_key": month_key,
        "record": {
            "thoi_gian": record.get("thoi_gian", ""),
            "bien_so": record.get("bien_so", ""),
            "hang_xe": record.get("hang_xe", ""),
            "dich_vu": record.get("dich_vu", ""),
            "gia": record.get("gia", ""),
            "nguoi_phu_trach": record.get("nguoi_phu_trach", ""),
        },
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            if data.get("success"):
                cfg = _load_local_config()
                if data.get("file_url"):
                    file_urls = cfg.get("drive_file_urls") or {}
                    file_urls[month_key] = data["file_url"]
                    cfg["drive_file_urls"] = file_urls
                if data.get("folder_url"):
                    cfg["drive_folder_url"] = data["folder_url"]
                _save_local_config(cfg)
                return {
                    "synced": True,
                    "file_url": data.get("file_url", ""),
                    "folder_url": data.get("folder_url", ""),
                }
            return {"synced": False, "error": data.get("error", "Unknown error")}
    except Exception as e:
        return {"synced": False, "error": str(e)}


def sync_delete_from_drive(month_key: str, row_id: int) -> dict:
    """Xóa dòng tương ứng trên file Google Drive của tháng đó."""
    webhook_url = get_drive_webhook_url()
    if not webhook_url:
        return {"synced": False}

    payload = {
        "action": "delete",
        "month_key": month_key,
        "row_id": row_id,
    }
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return {"synced": bool(data.get("success"))}
    except Exception:
        return {"synced": False}


def fetch_month_from_drive(month_key: str) -> dict:
    """
    Kéo dữ liệu của 1 tháng từ Google Drive về Server (dùng để đồng bộ/khôi phục khi Cloud Server khởi động lại).
    """
    webhook_url = get_drive_webhook_url()
    if not webhook_url:
        return {"success": False}

    query = urllib.parse.urlencode({"action": "list", "month_key": month_key})
    url = f"{webhook_url}?{query}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            if data.get("success"):
                cfg = _load_local_config()
                if data.get("file_url"):
                    file_urls = cfg.get("drive_file_urls") or {}
                    file_urls[month_key] = data["file_url"]
                    cfg["drive_file_urls"] = file_urls
                if data.get("folder_url"):
                    cfg["drive_folder_url"] = data["folder_url"]
                _save_local_config(cfg)
            return data
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_saved_drive_links(month_key: str) -> dict:
    cfg = _load_local_config()
    file_urls = cfg.get("drive_file_urls") or {}
    return {
        "configured": bool(get_drive_webhook_url()),
        "file_url": file_urls.get(month_key, ""),
        "folder_url": cfg.get("drive_folder_url", ""),
    }

