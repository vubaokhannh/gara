# Hướng Dẫn Kết Nối Google Drive & Public Lên Cloud 24/7

Hệ thống đã được tích hợp sẵn **Đồng bộ kép (Dual-Sync)**: vừa lưu file `.xlsx` theo từng tháng trên Server, vừa tự động tạo thư mục `Gara_Data` và tách mỗi tháng 1 file (`gara_11_2026`, `gara_12_2026`...) trên **Google Drive** của bạn.

---

## Bước 1: Tạo Link Kết Nối Google Drive (Chỉ mất 1 phút)

1. Mở trang **[Google Apps Script](https://script.google.com/)** (đăng nhập bằng tài khoản Google Drive của bạn).
2. Bấm nút **Dự án mới (New project)** ở góc trái trên.
3. Mở file [google_apps_script.gs](file:///Users/khanh/Workspace/garaxe/google_apps_script.gs) trong thư mục dự án này, **Copy toàn bộ nội dung** và dán đè vào khung soạn thảo trên Google Apps Script $\rightarrow$ Bấm biểu tượng 💾 **Lưu**.
4. Bấm nút màu xanh **Triển khai (Deploy)** ở góc phải trên $\rightarrow$ Chọn **Tùy chọn triển khai mới (New deployment)**:
   - Bấm biểu tượng ⚙️ (Chọn loại) $\rightarrow$ Chọn **Ứng dụng web (Web app)**.
   - **Thực thi dưới dạng (Execute as)**: Chọn **Tôi (Me)**.
   - **Ai có quyền truy cập (Who has access)**: Chọn **Bất kỳ ai (Anyone)**.
5. Bấm **Triển khai (Deploy)** $\rightarrow$ Bấm **Cấp quyền truy cập (Authorize access)** $\rightarrow$ Chọn tài khoản Google của bạn $\rightarrow$ Bấm *Advanced (Nâng cao)* $\rightarrow$ *Go to Untitled project (unsafe)* $\rightarrow$ **Allow (Cho phép)**.
6. Copy đường link **URL ứng dụng web (Web app URL)** (có dạng `https://script.google.com/macros/s/.../exec`).
7. Mở giao diện Web Gara Voice $\rightarrow$ Bấm nút **Drive & PIN** ở góc phải trên $\rightarrow$ Dán link vừa copy vào ô **Google Apps Script Webhook URL** và bấm **Lưu cài đặt**.

> Ngay lập tức, mỗi khi bạn bấm **Lưu Excel & Drive**, trên Google Drive của bạn sẽ tự động xuất hiện thư mục **`Gara_Data`** chứa file của từng tháng (`gara_11_2026`, `gara_12_2026`...).

---

## Bước 2: Đưa Lên Render.com Chạy 24/7 (Có sẵn HTTPS miễn phí)

1. Đẩy thư mục code `/Users/khanh/Workspace/garaxe` lên 1 kho lưu trữ (Repository) trên **GitHub** của bạn.
2. Truy cập **[Render.com](https://render.com/)** $\rightarrow$ Bấm **New +** $\rightarrow$ Chọn **Web Service** $\rightarrow$ Kết nối với kho GitHub vừa tạo.
3. Render sẽ tự động nhận diện cấu hình hoặc bạn điền:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4`
4. Trong mục **Environment Variables** trên Render, thêm 2 biến:
   - `APP_PIN`: Mã PIN 4 số cho nhân viên của bạn (ví dụ: `1234` hoặc `6868`).
   - `DRIVE_WEBHOOK_URL`: Dán đường link Google Apps Script ở Bước 1 vào đây.
5. Bấm **Deploy Web Service**. Sau 1–2 phút, bạn sẽ có đường link chính thức dạng `https://gara-voice.onrender.com` (mở được từ mọi điện thoại qua 4G/Wi-Fi và dùng được nút Mic trực tiếp 100%).

