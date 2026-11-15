# -*- coding: utf-8 -*-
import re
from datetime import datetime

# Danh sách các hãng & dòng xe Ô TÔ phổ biến tại Việt Nam để nhận diện chuẩn xác
KNOWN_BRANDS = {
    # Các hãng ô tô
    "toyota": "Toyota",
    "tô yô ta": "Toyota",
    "honda": "Honda",
    "hon da": "Honda",
    "mazda": "Mazda",
    "mát đa": "Mazda",
    "kia": "Kia",
    "hyundai": "Hyundai",
    "huyn đai": "Hyundai",
    "huyndai": "Hyundai",
    "vinfast": "VinFast",
    "vin phát": "VinFast",
    "ford": "Ford",
    "pho": "Ford",
    "mitsubishi": "Mitsubishi",
    "mít su bi shi": "Mitsubishi",
    "mít su": "Mitsubishi",
    "suzuki": "Suzuki",
    "su du ki": "Suzuki",
    "mercedes": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mẹc xê đét": "Mercedes-Benz",
    "mẹc": "Mercedes-Benz",
    "mec": "Mercedes-Benz",
    "bmw": "BMW",
    "bê mờ đúp": "BMW",
    "audi": "Audi",
    "au đi": "Audi",
    "lexus": "Lexus",
    "lếch xựt": "Lexus",
    "peugeot": "Peugeot",
    "pơ giô": "Peugeot",
    "subaru": "Subaru",
    "isuzu": "Isuzu",
    "nissan": "Nissan",
    "chevrolet": "Chevrolet",
    "volvo": "Volvo",
    "porsche": "Porsche",
    "land rover": "Land Rover",
    "range rover": "Range Rover",
    "mg": "MG",
    "byd": "BYD",
    "haval": "Haval",
    "skoda": "Skoda",
    "volkswagen": "Volkswagen",
    "mini cooper": "Mini Cooper",
    "jeep": "Jeep",
    "thaco": "Thaco",
    "hino": "Hino",
    # Các dòng xe Ô tô phổ biến -> tự động gắn Hãng + Dòng xe
    # Toyota
    "vios": "Toyota Vios",
    "innova": "Toyota Innova",
    "innova cross": "Toyota Innova Cross",
    "fortuner": "Toyota Fortuner",
    "camry": "Toyota Camry",
    "corolla cross": "Toyota Corolla Cross",
    "yaris cross": "Toyota Yaris Cross",
    "yaris": "Toyota Yaris",
    "veloz": "Toyota Veloz",
    "avanza": "Toyota Avanza",
    "raize": "Toyota Raize",
    "hilux": "Toyota Hilux",
    "land cruiser": "Toyota Land Cruiser",
    "prado": "Toyota Prado",
    "altis": "Toyota Altis",
    "wigo": "Toyota Wigo",
    # Honda Ô tô
    "civic": "Honda Civic",
    "crv": "Honda CR-V",
    "cr-v": "Honda CR-V",
    "hrv": "Honda HR-V",
    "hr-v": "Honda HR-V",
    "brv": "Honda BR-V",
    "br-v": "Honda BR-V",
    "city": "Honda City",
    "accord": "Honda Accord",
    "brio": "Honda Brio",
    # Mazda
    "cx5": "Mazda CX-5",
    "cx-5": "Mazda CX-5",
    "cx8": "Mazda CX-8",
    "cx-8": "Mazda CX-8",
    "cx3": "Mazda CX-3",
    "cx-3": "Mazda CX-3",
    "cx30": "Mazda CX-30",
    "cx-30": "Mazda CX-30",
    "mazda 2": "Mazda 2",
    "mazda2": "Mazda 2",
    "mazda 3": "Mazda 3",
    "mazda3": "Mazda 3",
    "mazda 6": "Mazda 6",
    "mazda6": "Mazda 6",
    "bt50": "Mazda BT-50",
    "bt-50": "Mazda BT-50",
    # Hyundai
    "accent": "Hyundai Accent",
    "santafe": "Hyundai SantaFe",
    "santa fe": "Hyundai SantaFe",
    "tucson": "Hyundai Tucson",
    "creta": "Hyundai Creta",
    "venue": "Hyundai Venue",
    "custin": "Hyundai Custin",
    "palisade": "Hyundai Palisade",
    "stargazer": "Hyundai Stargazer",
    "elantra": "Hyundai Elantra",
    "i10": "Hyundai i10",
    "grand i10": "Hyundai Grand i10",
    "kona": "Hyundai Kona",
    "solati": "Hyundai Solati",
    "porter": "Hyundai Porter",
    # Kia
    "morning": "Kia Morning",
    "seltos": "Kia Seltos",
    "sonet": "Kia Sonet",
    "carnival": "Kia Carnival",
    "sedona": "Kia Sedona",
    "sportage": "Kia Sportage",
    "sorento": "Kia Sorento",
    "k3": "Kia K3",
    "k5": "Kia K5",
    "cerato": "Kia Cerato",
    "soluto": "Kia Soluto",
    "carens": "Kia Carens",
    # Ford
    "ranger": "Ford Ranger",
    "raptor": "Ford Ranger Raptor",
    "everest": "Ford Everest",
    "territory": "Ford Territory",
    "explorer": "Ford Explorer",
    "ecosport": "Ford EcoSport",
    "transit": "Ford Transit",
    # Mitsubishi
    "xpander": "Mitsubishi Xpander",
    "xpander cross": "Mitsubishi Xpander Cross",
    "xforce": "Mitsubishi Xforce",
    "outlander": "Mitsubishi Outlander",
    "pajero sport": "Mitsubishi Pajero Sport",
    "pajero": "Mitsubishi Pajero",
    "triton": "Mitsubishi Triton",
    "attrage": "Mitsubishi Attrage",
    # VinFast Ô tô
    "vf3": "VinFast VF3",
    "vf 3": "VinFast VF3",
    "vf5": "VinFast VF5",
    "vf 5": "VinFast VF5",
    "vf6": "VinFast VF6",
    "vf 6": "VinFast VF6",
    "vf7": "VinFast VF7",
    "vf 7": "VinFast VF7",
    "vf8": "VinFast VF8",
    "vf 8": "VinFast VF8",
    "vf9": "VinFast VF9",
    "vf 9": "VinFast VF9",
    "vfe34": "VinFast VF e34",
    "vf e34": "VinFast VF e34",
    "fadil": "VinFast Fadil",
    "lux a": "VinFast Lux A2.0",
    "lux sa": "VinFast Lux SA2.0",
    # Suzuki & Isuzu
    "xl7": "Suzuki XL7",
    "ertiga": "Suzuki Ertiga",
    "jimny": "Suzuki Jimny",
    "swift": "Suzuki Swift",
    "ciaz": "Suzuki Ciaz",
    "dmax": "Isuzu D-Max",
    "d-max": "Isuzu D-Max",
    "mux": "Isuzu mu-X",
    "mu-x": "Isuzu mu-X",
    # Mercedes / BMW / Lexus
    "glc": "Mercedes GLC",
    "glc 200": "Mercedes GLC 200",
    "glc 300": "Mercedes GLC 300",
    "c200": "Mercedes C200",
    "c300": "Mercedes C300",
    "e200": "Mercedes E200",
    "e300": "Mercedes E300",
    "s450": "Mercedes S450",
}

# Danh sách dịch vụ GARA Ô TÔ phổ biến
KNOWN_SERVICES = [
    "bảo dưỡng cấp lớn",
    "bảo dưỡng cấp nhỏ",
    "bảo dưỡng định kỳ",
    "bảo dưỡng toàn diện",
    "bảo dưỡng phanh",
    "bảo dưỡng gầm",
    "bảo dưỡng điều hòa",
    "bảo dưỡng máy",
    "bảo dưỡng",
    "thay dầu hộp số tự động",
    "thay dầu hộp số",
    "thay dầu cầu",
    "thay dầu phanh",
    "thay dầu trợ lực lái",
    "thay dầu máy",
    "thay dầu động cơ",
    "thay dầu",
    "thay nhớt hộp số",
    "thay nhớt máy",
    "thay nhớt",
    "thay lọc dầu",
    "thay lọc nhớt",
    "thay lọc gió động cơ",
    "thay lọc gió điều hòa",
    "thay lọc gió",
    "thay lọc nhiên liệu",
    "thay lọc xăng",
    "thay nước làm mát",
    "súc rửa két nước",
    "thay má phanh",
    "thay bố thắng",
    "láng đĩa phanh",
    "vớt đĩa phanh",
    "thay ắc quy",
    "thay bình ắc quy",
    "kích bình ắc quy",
    "kích bình",
    "thay bugi",
    "thay dây curoa",
    "thay giảm xóc",
    "thay phuộc",
    "thay rotuyn",
    "thay cao su càng a",
    "thay lá côn",
    "làm máy",
    "đại tu động cơ",
    "đại tu hộp số",
    "hạ hộp số",
    "làm gầm",
    "sửa gầm",
    "sửa điện ô tô",
    "sửa điện",
    "sửa điều hòa",
    "sửa máy lạnh",
    "nạp gas điều hòa",
    "bơm gas máy lạnh",
    "thay lốc điều hòa",
    "cân chỉnh thước lái",
    "cân bằng động",
    "chỉnh độ chụm",
    "đảo lốp",
    "thay lốp",
    "vá lốp",
    "vệ sinh nội thất",
    "dọn nội thất",
    "vệ sinh khoang máy",
    "rửa khoang máy",
    "vệ sinh kim phun",
    "vệ sinh buồng đốt",
    "vệ sinh họng ga",
    "vệ sinh cổ hút",
    "vệ sinh dàn lạnh",
    "rửa xe bọt tuyết",
    "rửa xe chi tiết",
    "rửa gầm",
    "rửa xe",
    "đánh bóng sơn",
    "đánh bóng",
    "phủ ceramic",
    "phủ gầm chống rỉ",
    "phủ gầm",
    "dán phim cách nhiệt",
    "cách âm chống ồn",
    "sơn dặm",
    "sơn quây cả xe",
    "sơn quây",
    "sơn cản trước",
    "sơn cản sau",
    "sơn cửa xe",
    "sơn xe",
    "đồng sơn",
    "gò hàn",
    "phục hồi xe tai nạn",
    "lắp camera hành trình",
    "lắp màn hình android",
    "lắp cảm biến áp suất lốp",
    "độ đèn",
    "kiểm tra tổng quát",
    "đọc lỗi xóa lỗi",
    "cứu hộ giao thông",
    "cứu hộ",
]

VIET_DIGITS = {
    "không": "0",
    "linh": "0",
    "lẻ": "0",
    "một": "1",
    "mốt": "1",
    "hai": "2",
    "ba": "3",
    "bốn": "4",
    "tư": "4",
    "năm": "5",
    "lăm": "5",
    "sáu": "6",
    "bảy": "7",
    "bẩy": "7",
    "tám": "8",
    "chín": "9",
}


def parse_vietnamese_price(text: str):
    """
    Trích xuất giá tiền từ câu nói tiếng Việt.
    Hỗ trợ:
      - "50 nghìn", "50 ngàn", "50k", "50 cành" -> 50000
      - "150.000", "150,000", "150000" -> 150000
      - "1 triệu 500 nghìn", "1 triệu rưỡi", "1,5 triệu", "1 củ rưỡi" -> 1500000
      - "năm mươi nghìn", "hai trăm nghìn" -> 50000, 200000
    Trả về: (price_int, matched_substring)
    """
    lower = text.lower()

    # 1. Mẫu: X triệu Y (nghìn/trăm/rưỡi) (VD: "1 triệu 500 nghìn", "1 triệu rưỡi", "2 triệu 3")
    m_trieu = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:triệu|củ|tr)\s*(rưỡi|(\d+)\s*(?:nghìn|ngàn|k|trăm)?)?",
        lower,
    )
    if m_trieu:
        base_str = m_trieu.group(1).replace(",", ".")
        base_val = float(base_str) * 1_000_000
        extra_val = 0
        if m_trieu.group(2) == "rưỡi":
            extra_val = 500_000
        elif m_trieu.group(3):
            sub_num = int(m_trieu.group(3))
            full_match_str = m_trieu.group(0)
            if "nghìn" in full_match_str or "ngàn" in full_match_str or "k" in full_match_str:
                extra_val = sub_num * 1_000
            elif sub_num < 10:
                extra_val = sub_num * 100_000
            elif sub_num < 1000:
                extra_val = sub_num * 1_000
            else:
                extra_val = sub_num
        return int(base_val + extra_val), m_trieu.group(0)

    # 2. Mẫu: X trăm rưỡi (VD: "1 trăm rưỡi", "2 trăm rưỡi")
    m_tram_ruoi = re.search(r"(\d+)\s*trăm\s*rưỡi", lower)
    if m_tram_ruoi:
        val = int(m_tram_ruoi.group(1)) * 100_000 + 50_000
        return val, m_tram_ruoi.group(0)

    # 3. Mẫu: X nghìn / ngàn / k / cành / lít / trăm nghìn (VD: "50 nghìn", "50k", "150 ngàn", "2 lít")
    m_nghin = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(trăm\s*(?:nghìn|ngàn)|nghìn|ngàn|k|cành|lít)\b",
        lower,
    )
    if m_nghin:
        num_raw = m_nghin.group(1)
        unit = m_nghin.group(2)
        # Nếu viết kiểu "50.000 nghìn" thì bỏ dấu chấm
        if re.match(r"^\d{1,3}(\.\d{3})+$", num_raw):
            val = int(num_raw.replace(".", ""))
        else:
            num_val = float(num_raw.replace(",", "."))
            if "trăm" in unit or unit == "lít":
                val = int(num_val * 100_000)
            elif num_val < 1000:
                val = int(num_val * 1_000)
            else:
                val = int(num_val)
        return val, m_nghin.group(0)

    # 4. Mẫu số tiền viết đầy đủ có dấu chấm/phẩy hoặc >= 10000 (VD: "50.000", "150,000", "50000 đ")
    m_full_num = re.search(
        r"\b(\d{1,3}(?:[.,]\d{3})+|\d{5,9})\s*(?:đồng|vnd|vnđ|đ)?\b", lower
    )
    if m_full_num:
        raw_digits = re.sub(r"[.,]", "", m_full_num.group(1))
        return int(raw_digits), m_full_num.group(0)

    # 5. Mẫu số bằng chữ tiếng Việt cơ bản (VD: "năm mươi nghìn", "hai trăm nghìn")
    word_numbers = {
        "mười": 10,
        "hai mươi": 20,
        "ba mươi": 30,
        "bốn mươi": 40,
        "năm mươi": 50,
        "sáu mươi": 60,
        "bảy mươi": 70,
        "tám mươi": 80,
        "chín mươi": 90,
        "một trăm": 100,
        "hai trăm": 200,
        "ba trăm": 300,
        "bốn trăm": 400,
        "năm trăm": 500,
    }
    for word, mult in sorted(word_numbers.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{word}\s*(?:nghìn|ngàn)\b"
        m_word = re.search(pattern, lower)
        if m_word:
            return mult * 1000, m_word.group(0)

    return None, ""


def extract_license_plate(text: str):
    """
    Trích xuất và chuẩn hóa biển số xe Việt Nam.
    Ví dụ:
      - "51A 12345" -> "51A-12345"
      - "51A-123.45" -> "51A-123.45" (hoặc chuẩn hóa "51A-12345")
      - "29B1 45678" -> "29B1-45678"
      - "30F 9876" -> "30F-9876"
    Trả về: (plate_formatted, matched_substring)
    """
    # Loại bỏ từ khóa "biển số", "xe biển số", "bs" ở đầu để dễ bắt
    # Mẫu chuẩn biển số VN: 2 chữ số đầu (11-99) + 1-2 chữ cái (A-Z) + (tùy chọn 1 số/chữ cho xe máy) + 4-5 chữ số cuối
    plate_pattern = re.compile(
        r"\b(\d{2})\s*[-.]?\s*([A-Za-zĐđ]{1,2}\d?)\s*[-.]?\s*(\d{3}\s*[.]?\s*\d{2}|\d{4,5})\b"
    )
    match = plate_pattern.search(text)
    if match:
        province = match.group(1)
        series = match.group(2).upper()
        number_part = re.sub(r"\s+", "", match.group(3))
        formatted = f"{province}{series}-{number_part}"
        return formatted, match.group(0)

    return None, ""


def format_price_vn(price_int: int) -> str:
    """Định dạng số nguyên 50000 -> '50.000'"""
    if price_int is None:
        return ""
    return f"{int(price_int):,}".replace(",", ".")


def parse_price_input(price_val) -> int:
    """Chuyển đổi chuỗi giá ('50.000', '50000', '50,000') về số nguyên."""
    if isinstance(price_val, (int, float)):
        return int(price_val)
    if not price_val:
        return 0
    cleaned = re.sub(r"[^\d]", "", str(price_val))
    return int(cleaned) if cleaned else 0


def parse_voice_text(text: str) -> dict:
    """
    Phân tích câu nói của nhân viên thành cấu trúc dữ liệu chuẩn 6 trường:
      - thoi_gian (DD/MM/YYYY)
      - bien_so (VD: 51A-12345)
      - hang_xe (VD: Honda)
      - dich_vu (VD: Rửa xe)
      - gia (VD: 50000 - Không bắt buộc, có thể để trống)
      - nguoi_phu_trach (VD: Minh, Tuấn...)
    Đồng thời kiểm tra tính hợp lệ (Validation).
    """
    today_str = datetime.now().strftime("%d/%m/%Y")
    raw_text = (text or "").strip()

    if not raw_text:
        return {
            "raw_text": "",
            "thoi_gian": today_str,
            "bien_so": "",
            "hang_xe": "",
            "dich_vu": "",
            "gia": 0,
            "gia_hien_thi": "",
            "nguoi_phu_trach": "",
            "is_valid": False,
            "errors": ["Vui lòng nói hoặc nhập nội dung thông tin xe."],
        }

    working_text = raw_text

    # 1. Trích xuất Biển số xe
    bien_so, matched_plate = extract_license_plate(working_text)
    if matched_plate:
        working_text = working_text.replace(matched_plate, " , ", 1)

    # 2. Trích xuất Giá tiền (Không bắt buộc)
    gia, matched_price = parse_vietnamese_price(working_text)
    if matched_price:
        pattern_price = re.escape(matched_price)
        working_text = re.sub(pattern_price, " , ", working_text, count=1, flags=re.IGNORECASE)

    # 3. Trích xuất Người phụ trách nếu nói kèm từ khóa (VD: "phụ trách Minh", "thợ Tuấn", "nhân viên Nam", "anh Hùng làm")
    nguoi_phu_trach = ""
    m_staff = re.search(
        r"\b(?:người\s+phụ\s+trách|phụ\s+trách|nhân\s+viên|thợ\s+máy|thợ|kỹ\s+thuật|do|anh|em|bạn)\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)(?=\s*(?:[,.;]|làm|$))",
        working_text,
        flags=re.IGNORECASE,
    )
    if m_staff:
        candidate = m_staff.group(1).strip()
        if candidate.lower() not in KNOWN_BRANDS and not any(
            srv in candidate.lower() for srv in KNOWN_SERVICES
        ):
            nguoi_phu_trach = candidate.title()
            working_text = working_text.replace(m_staff.group(0), " , ", 1)

    # 4. Dọn các từ nối thừa ở đầu như "Xe ô tô", "Xe biển số", "biển số", "xe", "giá", "hết", "tổng"
    working_text = re.sub(
        r"^\s*(?:xe\s+ô\s+tô|ô\s+tô|xe)\b",
        " ",
        working_text,
        flags=re.IGNORECASE,
    )
    working_text = re.sub(
        r"\b(xe\s+biển\s+số|biển\s+số\s+xe|biển\s+số|biển|hãng\s+xe|dòng\s+xe|loại\s+xe|hãng|dịch\s+vụ|làm\s+dịch\s+vụ|giá\s+tiền|giá|hết\s+tổng|tổng\s+cộng|hết|đồng|vnđ|vnd|người\s+phụ\s+trách|phụ\s+trách)\b",
        " ",
        working_text,
        flags=re.IGNORECASE,
    )

    # 5. Trích xuất Hãng xe & Dịch vụ
    hang_xe = ""
    dich_vu = ""

    lower_working = working_text.lower()

    # Tìm hãng xe trong danh sách KNOWN_BRANDS trước
    for brand_key, brand_name in sorted(KNOWN_BRANDS.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(brand_key)}\b"
        m_brand = re.search(pattern, lower_working)
        if m_brand:
            hang_xe = brand_name
            working_text = re.sub(pattern, " , ", working_text, count=1, flags=re.IGNORECASE)
            break

    # Tìm dịch vụ và người phụ trách từ các phần còn lại ngăn cách bởi dấu phẩy
    remaining_parts = [
        p.strip(" .,-:;!?") for p in re.split(r"[,;]+", working_text) if p.strip(" .,-:;!?")
    ]

    if not hang_xe and len(remaining_parts) >= 2:
        first_part_lower = remaining_parts[0].lower()
        is_first_service = any(srv in first_part_lower for srv in KNOWN_SERVICES)
        if not is_first_service:
            hang_xe = remaining_parts[0].title()
            remaining_parts = remaining_parts[1:]

    # Nếu chưa bắt được người phụ trách bằng từ khóa, nhưng phần cuối cùng sau dấu phẩy là tên riêng ngắn (1-3 từ, không phải dịch vụ)
    if not nguoi_phu_trach and len(remaining_parts) >= 2:
        last_part = remaining_parts[-1].strip()
        last_lower = last_part.lower()
        is_last_service = any(srv in last_lower for srv in KNOWN_SERVICES)
        if not is_last_service and 1 <= len(last_part.split()) <= 3:
            nguoi_phu_trach = last_part.title()
            remaining_parts = remaining_parts[:-1]

    if remaining_parts:
        dich_vu_raw = ", ".join(remaining_parts)
        dich_vu_raw = re.sub(r"\s+", " ", dich_vu_raw).strip(" .,-")
        if dich_vu_raw:
            dich_vu = dich_vu_raw[0].upper() + dich_vu_raw[1:]

    # Fallback: Nếu vẫn chưa có dịch vụ, quét trong câu gốc theo KNOWN_SERVICES
    if not dich_vu:
        found_services = []
        temp_lower = raw_text.lower()
        for srv in KNOWN_SERVICES:
            if re.search(rf"\b{re.escape(srv)}\b", temp_lower):
                found_services.append(srv.capitalize())
                temp_lower = temp_lower.replace(srv, " ")
        if found_services:
            dich_vu = ", ".join(found_services)

    # 6. Kiểm tra tính hợp lệ (Giá tiền và Người phụ trách không bắt buộc, Giá có thể để trống)
    errors = []
    if not bien_so:
        errors.append("Chưa nhận diện được Biển số xe (VD: 51A-12345).")
    if not hang_xe:
        errors.append("Chưa nhận diện được Hãng xe (VD: Honda, Toyota...).")
    if not dich_vu:
        errors.append("Chưa nhận diện được Dịch vụ (VD: Rửa xe, Thay nhớt...).")

    return {
        "raw_text": raw_text,
        "thoi_gian": today_str,
        "bien_so": bien_so or "",
        "hang_xe": hang_xe or "",
        "dich_vu": dich_vu or "",
        "gia": gia or 0,
        "gia_hien_thi": format_price_vn(gia) if (gia and gia > 0) else "",
        "nguoi_phu_trach": nguoi_phu_trach or "",
        "is_valid": len(errors) == 0,
        "errors": errors,
    }


def validate_record(data: dict) -> tuple[bool, list[str], dict]:
    """
    Kiểm tra tính hợp lệ của dữ liệu trước khi ghi vào file Excel.
    Giá tiền có thể để trống (không bắt buộc).
    """
    thoi_gian = (data.get("thoi_gian") or datetime.now().strftime("%d/%m/%Y")).strip()
    bien_so = (data.get("bien_so") or "").strip().upper()
    hang_xe = (data.get("hang_xe") or "").strip()
    dich_vu = (data.get("dich_vu") or "").strip()
    nguoi_phu_trach = (data.get("nguoi_phu_trach") or "").strip()
    gia_int = parse_price_input(data.get("gia"))

    extracted_plate, _ = extract_license_plate(bien_so)
    if extracted_plate:
        bien_so = extracted_plate

    if hang_xe:
        hang_xe = hang_xe[0].upper() + hang_xe[1:]
    if dich_vu:
        dich_vu = dich_vu[0].upper() + dich_vu[1:]
    if nguoi_phu_trach:
        nguoi_phu_trach = nguoi_phu_trach.title()

    errors = []
    if not bien_so:
        errors.append("Biển số không được để trống.")
    if not hang_xe:
        errors.append("Hãng xe không được để trống.")
    if not dich_vu:
        errors.append("Dịch vụ không được để trống.")

    cleaned = {
        "thoi_gian": thoi_gian,
        "bien_so": bien_so,
        "hang_xe": hang_xe,
        "dich_vu": dich_vu,
        "gia": gia_int if gia_int > 0 else 0,
        "gia_hien_thi": format_price_vn(gia_int) if gia_int > 0 else "",
        "nguoi_phu_trach": nguoi_phu_trach,
    }

    return (len(errors) == 0), errors, cleaned

