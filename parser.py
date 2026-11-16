# -*- coding: utf-8 -*-
import re
from datetime import datetime

# Danh sách các hãng & dòng xe Ô TÔ phổ biến tại Việt Nam để nhận diện chuẩn xác
KNOWN_BRANDS = {
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
    # Toyota
    "toyota vios": "Toyota Vios",
    "toyota innova": "Toyota Innova",
    "toyota fortuner": "Toyota Fortuner",
    "toyota camry": "Toyota Camry",
    "toyota corolla cross": "Toyota Corolla Cross",
    "toyota cross": "Toyota Corolla Cross",
    "toyota yaris": "Toyota Yaris",
    "toyota veloz": "Toyota Veloz",
    "toyota avanza": "Toyota Avanza",
    "toyota raize": "Toyota Raize",
    "toyota hilux": "Toyota Hilux",
    "toyota altis": "Toyota Altis",
    "toyota wigo": "Toyota Wigo",
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
    "honda civic": "Honda Civic",
    "honda crv": "Honda CR-V",
    "honda cr-v": "Honda CR-V",
    "honda hrv": "Honda HR-V",
    "honda hr-v": "Honda HR-V",
    "honda city": "Honda City",
    "honda accord": "Honda Accord",
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
    "mazda cx5": "Mazda CX-5",
    "mazda cx-5": "Mazda CX-5",
    "mazda cx 5": "Mazda CX-5",
    "mazda cx8": "Mazda CX-8",
    "mazda cx-8": "Mazda CX-8",
    "mazda cx 8": "Mazda CX-8",
    "mazda cx3": "Mazda CX-3",
    "mazda cx-3": "Mazda CX-3",
    "mazda cx30": "Mazda CX-30",
    "mazda cx-30": "Mazda CX-30",
    "mazda 2": "Mazda 2",
    "mazda2": "Mazda 2",
    "mazda 3": "Mazda 3",
    "mazda3": "Mazda 3",
    "mazda 6": "Mazda 6",
    "mazda6": "Mazda 6",
    "mazda bt50": "Mazda BT-50",
    "mazda bt-50": "Mazda BT-50",
    "cx5": "Mazda CX-5",
    "cx-5": "Mazda CX-5",
    "cx8": "Mazda CX-8",
    "cx-8": "Mazda CX-8",
    "cx3": "Mazda CX-3",
    "cx-3": "Mazda CX-3",
    "cx30": "Mazda CX-30",
    "cx-30": "Mazda CX-30",
    "bt50": "Mazda BT-50",
    "bt-50": "Mazda BT-50",
    # Hyundai
    "hyundai accent": "Hyundai Accent",
    "hyundai santafe": "Hyundai SantaFe",
    "hyundai santa fe": "Hyundai SantaFe",
    "hyundai tucson": "Hyundai Tucson",
    "hyundai creta": "Hyundai Creta",
    "hyundai elantra": "Hyundai Elantra",
    "hyundai i10": "Hyundai i10",
    "hyundai grand i10": "Hyundai Grand i10",
    "hyundai kona": "Hyundai Kona",
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
    "kia morning": "Kia Morning",
    "kia seltos": "Kia Seltos",
    "kia sonet": "Kia Sonet",
    "kia carnival": "Kia Carnival",
    "kia sedona": "Kia Sedona",
    "kia sportage": "Kia Sportage",
    "kia sorento": "Kia Sorento",
    "kia k3": "Kia K3",
    "kia k5": "Kia K5",
    "kia cerato": "Kia Cerato",
    "kia soluto": "Kia Soluto",
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
    "ford ranger": "Ford Ranger",
    "ford raptor": "Ford Ranger Raptor",
    "ford everest": "Ford Everest",
    "ford territory": "Ford Territory",
    "ford explorer": "Ford Explorer",
    "ford transit": "Ford Transit",
    "ranger": "Ford Ranger",
    "raptor": "Ford Ranger Raptor",
    "everest": "Ford Everest",
    "territory": "Ford Territory",
    "explorer": "Ford Explorer",
    "ecosport": "Ford EcoSport",
    "transit": "Ford Transit",
    # Mitsubishi
    "mitsubishi xpander": "Mitsubishi Xpander",
    "mitsubishi xforce": "Mitsubishi Xforce",
    "mitsubishi outlander": "Mitsubishi Outlander",
    "mitsubishi pajero": "Mitsubishi Pajero",
    "mitsubishi triton": "Mitsubishi Triton",
    "xpander": "Mitsubishi Xpander",
    "xpander cross": "Mitsubishi Xpander Cross",
    "xforce": "Mitsubishi Xforce",
    "outlander": "Mitsubishi Outlander",
    "pajero sport": "Mitsubishi Pajero Sport",
    "pajero": "Mitsubishi Pajero",
    "triton": "Mitsubishi Triton",
    "attrage": "Mitsubishi Attrage",
    # VinFast Ô tô
    "vinfast vf3": "VinFast VF3",
    "vinfast vf 3": "VinFast VF3",
    "vinfast vf5": "VinFast VF5",
    "vinfast vf 5": "VinFast VF5",
    "vinfast vf6": "VinFast VF6",
    "vinfast vf 6": "VinFast VF6",
    "vinfast vf7": "VinFast VF7",
    "vinfast vf 7": "VinFast VF7",
    "vinfast vf8": "VinFast VF8",
    "vinfast vf 8": "VinFast VF8",
    "vinfast vf9": "VinFast VF9",
    "vinfast vf 9": "VinFast VF9",
    "vinfast fadil": "VinFast Fadil",
    "vinfast lux a": "VinFast Lux A2.0",
    "vinfast lux sa": "VinFast Lux SA2.0",
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

# Các từ khóa thuộc nhóm dịch vụ "Đồng Sơn TM"
DONG_SON_KEYWORDS = [
    "đồng sơn tm",
    "đồng sơn thương mại",
    "đồng sơn",
    "sơn dặm",
    "sơn quây cả xe",
    "sơn quây",
    "sơn cản trước",
    "sơn cản sau",
    "sơn cửa",
    "sơn capo",
    "sơn cốp",
    "sơn tai xe",
    "sơn lazang",
    "sơn mâm",
    "sơn xe",
    "gò hàn",
    "gò nắn",
    "làm đồng",
    "đánh bóng sơn",
    "đánh bóng",
    "phủ ceramic",
    "phủ gầm",
    "phục hồi xe tai nạn",
]

# Danh sách Nội dung công việc phổ biến tại Gara Ô tô
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
    "làm đồng",
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

SERVICE_TYPES = ["Bảo Trì & Sửa Chữa", "Đồng Sơn TM"]
PAYMENT_METHODS = ["Chưa Thanh Toán", "Tiền Mặt", "Chuyển Khoản"]


def parse_vietnamese_price(text: str):
    """
    Trích xuất Báo Giá Dịch Vụ từ câu nói tiếng Việt.
    Trả về: (price_int, matched_substring)
    """
    lower = text.lower()

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

    m_tram_ruoi = re.search(r"(\d+)\s*trăm\s*rưỡi", lower)
    if m_tram_ruoi:
        val = int(m_tram_ruoi.group(1)) * 100_000 + 50_000
        return val, m_tram_ruoi.group(0)

    m_nghin = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(trăm\s*(?:nghìn|ngàn)|nghìn|ngàn|k|cành|lít)\b",
        lower,
    )
    if m_nghin:
        num_raw = m_nghin.group(1)
        unit = m_nghin.group(2)
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

    m_full_num = re.search(
        r"\b(\d{1,3}(?:[.,]\d{3})+|\d{5,9})\s*(?:đồng|vnd|vnđ|đ)?\b", lower
    )
    if m_full_num:
        raw_digits = re.sub(r"[.,]", "", m_full_num.group(1))
        return int(raw_digits), m_full_num.group(0)

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
    Trả về: (plate_formatted, matched_substring)
    """
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
    if not price_int or int(price_int) <= 0:
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


# ---------------------------------------------------------------------------
# CHUYỂN SỐ ĐỌC BẰNG CHỮ -> CHỮ SỐ (trước khi tách thông tin)
# VD: "một triệu hai" -> "1 triệu 2", "năm mươi mốt a một hai ba bốn năm" -> "51A 12345"
# ---------------------------------------------------------------------------
_PLATE_DIGITS = {
    "không": 0, "một": 1, "hai": 2, "ba": 3, "bốn": 4, "năm": 5,
    "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9,
}
_UNIT_DIGITS = {**_PLATE_DIGITS, "mốt": 1, "tư": 4, "lăm": 5}
_BIG_UNITS = {"nghìn", "ngàn", "triệu"}
_NUM_WORDS = set(_UNIT_DIGITS) | _BIG_UNITS | {"mười", "mươi", "trăm", "linh", "lẻ"}
_NUM_MARKERS = _BIG_UNITS | {"trăm", "mươi", "mười"}
_PUNCT = ",.;:!?"


def _core(token: str) -> str:
    return token.strip(_PUNCT).lower()


def _trail(token: str) -> str:
    return token[len(token.rstrip(_PUNCT)):]


def _is_letter(token: str) -> bool:
    c = _core(token)
    return len(c) == 1 and c.isalpha()


def _parse_small(words: list):
    """Đọc số dưới 1000: ['hai','trăm','năm','mươi'] -> 250."""
    total, cur = 0, None
    for w in words:
        if w in _UNIT_DIGITS:
            cur = _UNIT_DIGITS[w]
        elif w == "trăm":
            total += (cur if cur is not None else 1) * 100
            cur = None
        elif w == "mười":
            total += 10
            cur = None
        elif w == "mươi":
            total += (cur if cur is not None else 1) * 10
            cur = None
    return total + (cur or 0)


def _convert_number_run(words: list):
    """Đổi 1 cụm số chữ thành dạng 'N triệu M nghìn' để bộ tách giá hiểu được."""
    out, seg = [], []
    for w in words:
        if w in _BIG_UNITS:
            if not seg:
                return None
            out.append(f"{_parse_small(seg)} {w}")
            seg = []
        else:
            seg.append(w)
    if seg:
        out.append(str(_parse_small(seg)))
    return " ".join(out)


def _try_spoken_plate(tokens: list, i: int):
    """Nhận diện biển số đọc bằng chữ tại vị trí i. Trả về (chuỗi biển, vị trí kế tiếp) hoặc None."""
    n = len(tokens)
    t = _core(tokens[i])
    j = i + 1

    if re.fullmatch(r"\d{2}", t):
        prov = t
    elif t in _PLATE_DIGITS and i + 1 < n and _core(tokens[i + 1]) == "mươi" or t == "mười":
        base = 10 if t == "mười" else _PLATE_DIGITS[t] * 10
        if t != "mười":
            j = i + 2
        unit = 0
        if j + 1 < n and _core(tokens[j]) in _UNIT_DIGITS and _is_letter(tokens[j + 1]):
            unit = _UNIT_DIGITS[_core(tokens[j])]
            j += 1
        prov = str(base + unit)
    elif t in _PLATE_DIGITS and i + 2 < n and _core(tokens[i + 1]) in _PLATE_DIGITS and _is_letter(tokens[i + 2]):
        prov = f"{_PLATE_DIGITS[t]}{_PLATE_DIGITS[_core(tokens[i + 1])]}"
        j = i + 2
    else:
        return None

    if j >= n or not _is_letter(tokens[j]):
        return None
    letters = _core(tokens[j])
    j += 1
    if j < n and _is_letter(tokens[j]):
        letters += _core(tokens[j])
        j += 1

    digits = ""
    while j < n and len(digits) < 5:
        c = _core(tokens[j])
        if c in _PLATE_DIGITS:
            digits += str(_PLATE_DIGITS[c])
        elif re.fullmatch(r"\d", c):
            digits += c
        else:
            break
        j += 1
    if len(digits) < 4:
        return None
    return f"{prov}{letters.upper()} {digits}{_trail(tokens[j - 1])}", j


def normalize_spoken_numbers(text: str) -> str:
    """Đổi biển số và số tiền đọc bằng chữ sang chữ số."""
    tokens = (text or "").split()
    out, i, n = [], 0, len(tokens)
    while i < n:
        plate = _try_spoken_plate(tokens, i)
        if plate:
            out.append(plate[0])
            i = plate[1]
            continue

        # Số điện thoại đọc từng chữ số: "không chín không một hai ba bốn năm sáu bảy"
        if _core(tokens[i]) in _PLATE_DIGITS:
            j = i
            digits = ""
            while j < n and _core(tokens[j]) in _PLATE_DIGITS:
                digits += str(_PLATE_DIGITS[_core(tokens[j])])
                j += 1
            if len(digits) >= 9:
                out.append(digits + _trail(tokens[j - 1]))
                i = j
                continue

        if _core(tokens[i]) in _NUM_WORDS:
            j = i
            while j < n and _core(tokens[j]) in _NUM_WORDS:
                j += 1
            words = [_core(t) for t in tokens[i:j]]
            if any(w in _NUM_MARKERS for w in words):
                tail = ""
                if words[-1] == "trăm" and j < n and _core(tokens[j]) == "rưỡi":
                    words, tail = words[:-1], " trăm"
                converted = _convert_number_run(words)
                if converted:
                    out.append(converted + tail + _trail(tokens[j - 1]))
                    i = j
                    continue
        out.append(tokens[i])
        i += 1
    return " ".join(out)


# ---------------------------------------------------------------------------
# SỐ ĐIỆN THOẠI & TÊN KHÁCH HÀNG
# ---------------------------------------------------------------------------
_PHONE_RE = re.compile(
    r"(?:(?:số\s+)?(?:điện\s+thoại|sđt|đt)\s*[:,-]?\s*)?"
    r"(?<![\d.,])((?:\+?84|0)(?:[\s.\-]?\d){8,9})(?!\d)",
    flags=re.IGNORECASE,
)
_NAME_RE = re.compile(
    r"\b(?:tên\s+khách\s+hàng|tên\s+khách|khách\s+hàng|chủ\s+xe)\s+(?:là\s+)?"
    r"(?:(?:anh|chị|cô|chú|bác|ông|bà)\s+)?"
    r"([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+){0,3})",
    flags=re.IGNORECASE,
)
_NAME_STOP = {
    "số", "sđt", "đt", "điện", "biển", "xe", "thay", "sơn", "bảo", "rửa", "làm", "vệ", "đồng", "kiểm",
    "cân", "nạp", "sửa", "đánh", "phủ", "hạ", "đại", "thợ", "tiền", "chuyển", "chưa", "nợ", "giá", "báo",
    "ghi", "lưu", "hẹn", "người", "thực", "phụ", "kích", "độ", "lắp", "dán", "cứu", "đọc", "súc", "vớt", "láng",
}


def normalize_phone(raw: str) -> str:
    """'0901 234 567' / '+84 901 234 567' -> '0901234567'. Trả về '' nếu rỗng."""
    digits = re.sub(r"\D", "", str(raw or ""))
    if digits.startswith("84") and len(digits) in (11, 12):
        digits = "0" + digits[2:]
    return digits


def extract_phone(text: str):
    """Trả về (số_điện_thoại_chuẩn_hóa, đoạn_khớp_để_xóa_khỏi_câu)."""
    m = _PHONE_RE.search(text)
    if not m:
        return "", ""
    phone = normalize_phone(m.group(1))
    if not (9 <= len(phone) <= 11):
        return "", ""
    return phone, m.group(0)


def extract_customer_name(text: str):
    """Trả về (tên_khách, đoạn_khớp_để_xóa_khỏi_câu). Tên dừng trước từ khóa dịch vụ / hãng xe."""
    m = _NAME_RE.search(text)
    if not m:
        return "", ""
    kept = []
    for w in m.group(1).split():
        if w.lower() in _NAME_STOP or w.lower() in KNOWN_BRANDS or any(ch.isdigit() for ch in w):
            break
        kept.append(w)
    if not kept:
        return "", ""
    name = " ".join(kept)
    # đoạn cần xóa: từ đầu cụm khóa tới hết phần tên giữ lại
    start = m.start()
    tail_pos = m.start(1)
    for w in kept:
        tail_pos = text.index(w, tail_pos) + len(w)
    return name.title(), text[start:tail_pos]


def parse_voice_text(text: str) -> dict:
    """
    Phân tích câu nói của nhân viên thành cấu trúc 10 cột chuẩn của Gara Ô tô:
      1. stt (Tự động đánh số khi lưu)
      2. ngay (DD/MM/YYYY)
      3. bien_so (VD: 51A-12345)
      4. hieu_xe (VD: Mazda CX-5)
      5. dich_vu ("Bảo Trì & Sửa Chữa" hoặc "Đồng Sơn TM")
      6. noi_dung (VD: Thay dầu máy, bảo dưỡng phanh...)
      7. bao_gia (Số nguyên, có thể để trống) & bao_gia_hien_thi (VD: 850.000)
      8. thanh_toan ("Tiền Mặt" | "Chuyển Khoản" | "Chưa Thanh Toán")
      9. nguoi_thuc_hien (VD: Minh)
      10. ghi_chu (VD: Khách hẹn chiều lấy)
    """
    today_str = datetime.now().strftime("%d/%m/%Y")
    raw_text = (text or "").strip()

    if not raw_text:
        return {
            "raw_text": "",
            "ngay": today_str,
            "bien_so": "",
            "hieu_xe": "",
            "dich_vu": "Bảo Trì & Sửa Chữa",
            "noi_dung": "",
            "bao_gia": 0,
            "bao_gia_hien_thi": "",
            "thanh_toan": "Chưa Thanh Toán",
            "nguoi_thuc_hien": "",
            "ghi_chu": "",
            "so_dien_thoai": "",
            "ten_khach_hang": "",
            "is_valid": False,
            "errors": ["Vui lòng nói hoặc nhập thông tin xe."],
        }

    norm_text = normalize_spoken_numbers(raw_text)
    working_text = norm_text

    # 1. Trích xuất Ghi chú (nếu nói "ghi chú ...", "lưu ý ...", hoặc "hẹn ...")
    ghi_chu = ""
    m_note = re.search(
        r"\b((?:ghi\s+chú|lưu\s+ý|khách\s+hẹn|khách\s+báo)\s*[:,-]?\s*(.+)|(?:hẹn|hẹn\s+khách)\s+(?:chiều|sáng|trưa|tối|ngày|\d+).+)$",
        working_text,
        flags=re.IGNORECASE,
    )
    if m_note:
        raw_note = m_note.group(2) if m_note.group(2) else m_note.group(1)
        ghi_chu = (raw_note or "").strip(" .,-")
        if ghi_chu:
            ghi_chu = ghi_chu[0].upper() + ghi_chu[1:]
        working_text = working_text[: m_note.start()]

    # 1a. Tên / SĐT khách nói SAU phần "ghi chú" (VD: "ghi chú khách lấy 5 giờ tên khách Lan") -> tách ra khỏi ghi chú.
    # Chỉ nhận dạng "tên khách ..." (không nhận "khách hàng quen" vì đó là nội dung ghi chú).
    note_phone = note_name = ""
    if ghi_chu:
        note_phone, matched_np = extract_phone(ghi_chu)
        if matched_np:
            ghi_chu = ghi_chu.replace(matched_np, " ", 1)
        if re.search(r"tên\s+khách", ghi_chu, flags=re.IGNORECASE):
            note_name, matched_nn = extract_customer_name(ghi_chu)
            if matched_nn:
                ghi_chu = ghi_chu.replace(matched_nn, " ", 1)
        ghi_chu = re.sub(r"\s+", " ", ghi_chu).strip(" .,-")
        if ghi_chu:
            ghi_chu = ghi_chu[0].upper() + ghi_chu[1:]

    # 1b. Số điện thoại & tên khách hàng (trước biển số và giá để số điện thoại không bị nhận nhầm)
    so_dien_thoai, matched_phone = extract_phone(working_text)
    if matched_phone:
        working_text = working_text.replace(matched_phone, " , ", 1)
    ten_khach_hang, matched_name = extract_customer_name(working_text)
    if matched_name:
        working_text = working_text.replace(matched_name, " , ", 1)

    so_dien_thoai = so_dien_thoai or note_phone
    ten_khach_hang = ten_khach_hang or note_name

    # 2. Trích xuất Biển số xe
    bien_so, matched_plate = extract_license_plate(working_text)
    if matched_plate:
        working_text = working_text.replace(matched_plate, " , ", 1)

    # 3. Trích xuất Báo giá dịch vụ (Không bắt buộc)
    bao_gia, matched_price = parse_vietnamese_price(working_text)
    if matched_price:
        pattern_price = re.escape(matched_price)
        working_text = re.sub(pattern_price, " , ", working_text, count=1, flags=re.IGNORECASE)

    # 4. Trích xuất Hình thức Thanh Toán (Tiền Mặt | Chuyển Khoản | Chưa Thanh Toán)
    thanh_toan = "Chưa Thanh Toán"
    m_payment = re.search(
        r"\b(chưa\s+thanh\s+toán|tiền\s+mặt|chuyển\s+khoản|nợ)\b",
        working_text,
        flags=re.IGNORECASE,
    )
    if m_payment:
        pm_raw = m_payment.group(1).lower()
        if "tiền mặt" in pm_raw:
            thanh_toan = "Tiền Mặt"
        elif "chuyển khoản" in pm_raw:
            thanh_toan = "Chuyển Khoản"
        else:
            thanh_toan = "Chưa Thanh Toán"
        working_text = re.sub(
            r"\b(?:thanh\s+toán\s*)?" + re.escape(m_payment.group(0)) + r"\b",
            " , ",
            working_text,
            count=1,
            flags=re.IGNORECASE,
        )

    # 5. Trích xuất Người thực hiện
    nguoi_thuc_hien = ""
    m_staff = re.search(
        r"\b(?:người\s+thực\s+hiện|thực\s+hiện|người\s+phụ\s+trách|phụ\s+trách|nhân\s+viên|thợ\s+máy|thợ|kỹ\s+thuật|do|anh|em|bạn)\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)(?=\s*(?:[,.;]|làm|$))",
        working_text,
        flags=re.IGNORECASE,
    )
    if m_staff:
        candidate = m_staff.group(1).strip()
        candidate = re.sub(r"\s+(?:làm|phụ\s+trách|thực\s+hiện)$", "", candidate, flags=re.IGNORECASE).strip()
        if candidate.lower() not in KNOWN_BRANDS and not any(
            srv in candidate.lower() for srv in KNOWN_SERVICES
        ):
            nguoi_thuc_hien = candidate.title()
            working_text = working_text.replace(m_staff.group(0), " , ", 1)

    # 6. Nhận diện nhóm Dịch vụ ("Bảo Trì & Sửa Chữa" vs "Đồng Sơn TM")
    dich_vu = "Bảo Trì & Sửa Chữa"
    lower_raw = norm_text.lower()
    if any(ds_kw in lower_raw for ds_kw in DONG_SON_KEYWORDS):
        dich_vu = "Đồng Sơn TM"

    # Nếu nhân viên đọc rõ tên nhóm dịch vụ ("đồng sơn thương mại", "đồng sơn tm", "bảo trì sửa chữa") thì xóa khỏi phần Nội dung
    working_text = re.sub(
        r"\b(bảo\s+trì\s*(?:và|&)?\s*sửa\s+chữa|đồng\s+sơn\s+thương\s+mại|đồng\s+sơn\s+tm)\b",
        " , ",
        working_text,
        flags=re.IGNORECASE,
    )

    # 7. Dọn các từ nối thừa
    working_text = re.sub(
        r"^\s*(?:xe\s+ô\s+tô|ô\s+tô|xe)\b",
        " ",
        working_text,
        flags=re.IGNORECASE,
    )
    working_text = re.sub(
        r"\b(xe\s+biển\s+số|biển\s+số\s+xe|biển\s+số|biển|hiệu\s+xe|hãng\s+xe|dòng\s+xe|loại\s+xe|hãng|nội\s+dung|làm\s+dịch\s+vụ|dịch\s+vụ|báo\s+giá\s+dịch\s+vụ|báo\s+giá|giá\s+tiền|giá|thanh\s+toán|hết\s+tổng|tổng\s+cộng|hết|đồng|vnđ|vnd|người\s+thực\s+hiện|người\s+phụ\s+trách|phụ\s+trách|thực\s+hiện)\b",
        " ",
        working_text,
        flags=re.IGNORECASE,
    )

    # 8. Trích xuất Hiệu Xe & Nội Dung
    hieu_xe = ""
    noi_dung = ""

    lower_working = working_text.lower()
    for brand_key, brand_name in sorted(KNOWN_BRANDS.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(brand_key)}\b"
        m_brand = re.search(pattern, lower_working)
        if m_brand:
            hieu_xe = brand_name
            working_text = re.sub(pattern, " , ", working_text, count=1, flags=re.IGNORECASE)
            break

    remaining_parts = [
        p.strip(" .,-:;!?") for p in re.split(r"[,;]+", working_text) if p.strip(" .,-:;!?")
    ]

    if not hieu_xe and len(remaining_parts) >= 2:
        first_part_lower = remaining_parts[0].lower()
        is_first_service = any(srv in first_part_lower for srv in KNOWN_SERVICES)
        if not is_first_service:
            hieu_xe = remaining_parts[0].title()
            remaining_parts = remaining_parts[1:]

    if not nguoi_thuc_hien and len(remaining_parts) >= 2:
        last_part = remaining_parts[-1].strip()
        last_lower = last_part.lower()
        is_last_service = any(srv in last_lower for srv in KNOWN_SERVICES)
        if not is_last_service and 1 <= len(last_part.split()) <= 3:
            nguoi_thuc_hien = last_part.title()
            remaining_parts = remaining_parts[:-1]

    if remaining_parts:
        noi_dung_raw = ", ".join(remaining_parts)
        noi_dung_raw = re.sub(r"\s+", " ", noi_dung_raw).strip(" .,-")
        if noi_dung_raw:
            noi_dung = noi_dung_raw[0].upper() + noi_dung_raw[1:]

    if not noi_dung:
        found_services = []
        temp_lower = norm_text.lower()
        for srv in KNOWN_SERVICES:
            if re.search(rf"\b{re.escape(srv)}\b", temp_lower):
                found_services.append(srv.capitalize())
                temp_lower = temp_lower.replace(srv, " ")
        if found_services:
            noi_dung = ", ".join(found_services)

    # Kiểm tra lại nếu Nội dung thuộc nhóm Đồng Sơn
    if any(ds_kw in (noi_dung or "").lower() for ds_kw in DONG_SON_KEYWORDS):
        dich_vu = "Đồng Sơn TM"

    # 9. Kiểm tra tính hợp lệ (Báo giá, Người thực hiện, Ghi chú không bắt buộc)
    errors = []
    if not bien_so:
        errors.append("Chưa nhận diện được Biển Số (VD: 51A-12345).")
    if not hieu_xe:
        errors.append("Chưa nhận diện được Hiệu Xe (VD: Mazda CX-5, Toyota Vios...).")
    if not noi_dung:
        errors.append("Chưa nhận diện được Nội Dung công việc (VD: Thay dầu máy, Sơn cản...).")

    return {
        "raw_text": raw_text,
        "ngay": today_str,
        "bien_so": bien_so or "",
        "hieu_xe": hieu_xe or "",
        "dich_vu": dich_vu,
        "noi_dung": noi_dung or "",
        "bao_gia": bao_gia or 0,
        "bao_gia_hien_thi": format_price_vn(bao_gia) if (bao_gia and bao_gia > 0) else "",
        "thanh_toan": thanh_toan,
        "nguoi_thuc_hien": nguoi_thuc_hien or "",
        "ghi_chu": ghi_chu or "",
        "so_dien_thoai": so_dien_thoai,
        "ten_khach_hang": ten_khach_hang,
        "is_valid": len(errors) == 0,
        "errors": errors,
    }


def validate_record(data: dict) -> tuple[bool, list[str], dict]:
    """
    Kiểm tra tính hợp lệ và chuẩn hóa 10 trường trước khi lưu vào Excel & Google Drive.
    """
    ngay = (data.get("ngay") or data.get("thoi_gian") or datetime.now().strftime("%d/%m/%Y")).strip()
    bien_so = (data.get("bien_so") or "").strip().upper()
    hieu_xe = (data.get("hieu_xe") or data.get("hang_xe") or "").strip()
    dich_vu = (data.get("dich_vu") or "Bảo Trì & Sửa Chữa").strip()
    noi_dung = (data.get("noi_dung") or "").strip()
    bao_gia_int = parse_price_input(data.get("bao_gia") if "bao_gia" in data else data.get("gia"))
    thanh_toan = (data.get("thanh_toan") or "Chưa Thanh Toán").strip()
    nguoi_thuc_hien = (data.get("nguoi_thuc_hien") or data.get("nguoi_phu_trach") or "").strip()
    ghi_chu = (data.get("ghi_chu") or "").strip()
    raw_phone = str(data.get("so_dien_thoai") or "").strip()
    so_dien_thoai = normalize_phone(raw_phone)
    ten_khach_hang = (data.get("ten_khach_hang") or "").strip()
    if ten_khach_hang:
        ten_khach_hang = ten_khach_hang.title()

    extracted_plate, _ = extract_license_plate(bien_so)
    if extracted_plate:
        bien_so = extracted_plate

    if hieu_xe:
        hieu_xe = hieu_xe[0].upper() + hieu_xe[1:]
    if noi_dung:
        noi_dung = noi_dung[0].upper() + noi_dung[1:]
    if nguoi_thuc_hien:
        nguoi_thuc_hien = nguoi_thuc_hien.title()
    if dich_vu not in SERVICE_TYPES:
        dich_vu = "Đồng Sơn TM" if "đồng sơn" in dich_vu.lower() else "Bảo Trì & Sửa Chữa"
    if thanh_toan not in PAYMENT_METHODS:
        if "tiền mặt" in thanh_toan.lower():
            thanh_toan = "Tiền Mặt"
        elif "chuyển khoản" in thanh_toan.lower():
            thanh_toan = "Chuyển Khoản"
        else:
            thanh_toan = "Chưa Thanh Toán"

    errors = []
    if not bien_so:
        errors.append("Biển Số không được để trống.")
    if not hieu_xe:
        errors.append("Hiệu Xe không được để trống.")
    if not noi_dung:
        errors.append("Nội Dung công việc không được để trống.")
    if raw_phone and not re.fullmatch(r"0\d{8,10}", so_dien_thoai):
        errors.append("Số Điện Thoại không hợp lệ (VD: 0901234567).")

    cleaned = {
        "ngay": ngay,
        "bien_so": bien_so,
        "hieu_xe": hieu_xe,
        "dich_vu": dich_vu,
        "noi_dung": noi_dung,
        "bao_gia": bao_gia_int if bao_gia_int > 0 else 0,
        "bao_gia_hien_thi": format_price_vn(bao_gia_int) if bao_gia_int > 0 else "",
        "thanh_toan": thanh_toan,
        "nguoi_thuc_hien": nguoi_thuc_hien,
        "ghi_chu": ghi_chu,
        "so_dien_thoai": so_dien_thoai,
        "ten_khach_hang": ten_khach_hang,
    }

    return (len(errors) == 0), errors, cleaned
