# Hệ Thống Nhập Liệu Gara Bằng Giọng Nói (Mỗi Tháng 1 File Excel)

Ứng dụng giúp nhân viên gara chỉ cần nói câu thông tin (VD: *"Xe biển số 51A 12345, Honda, rửa xe, 50 nghìn."*), hệ thống sẽ tự động nhận diện, kiểm tra tính hợp lệ và **ghi trực tiếp vào file Excel của tháng tương ứng** (ví dụ: `data/gara_11_2026.xlsx`) mà không cần Database.

## Công nghệ sử dụng
- **Nhận giọng nói**: Web Speech API (`vi-VN`) hoặc nhập giọng nói bằng bàn phím điện thoại.
- **Kết nối Điện thoại $\leftrightarrow$ Máy tính**: Python Flask (`0.0.0.0:5000`).
- **Xử lý & Kiểm tra dữ liệu**: Python (`parser.py`).
- **Ghi & Lưu dữ liệu theo tháng**: OpenPyXL (`excel_manager.py`) tự động tách mỗi tháng 1 file `.xlsx` riêng trong thư mục `data/` (`gara_MM_YYYY.xlsx`).

## Cách chạy ứng dụng

```bash
# Chạy server Flask bằng môi trường ảo đã cài đặt sẵn
.venv/bin/python app.py
```

- **Trên máy tính**: Mở `http://127.0.0.1:5000`
- **Trên điện thoại**: Kết nối cùng mạng Wi-Fi với máy tính và mở địa chỉ IP hiển thị trên màn hình Terminal (hoặc góc phải trên giao diện Web, ví dụ `http://192.168.1.x:5000`).
