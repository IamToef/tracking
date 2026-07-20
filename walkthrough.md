# Walkthrough: Hoàn Thành Cấu Hình & Hướng Dẫn Deploy Lên Cloud

Chúng ta đã hoàn thành việc chuẩn bị và cấu hình dự án để sẵn sàng deploy lên dịch vụ Cloud Render. Dưới đây là tóm tắt các thay đổi đã thực hiện, kết quả kiểm thử và hướng dẫn chi tiết các bước tiếp theo để bạn có thể gửi cho người dùng ngoài Hà Nội sử dụng.

---

## 🛠️ Các Thay Đổi Đã Thực Hiện

### 1. Tạo tệp [requirements.txt](file:///d:/baihoc/Pet%20project/tracking/requirements.txt) [NEW]
Đã khai báo các thư viện cần thiết phục vụ cho việc build ứng dụng trên máy chủ đám mây:
* `fastapi==0.111.0`
* `uvicorn==0.30.1`
* `pydantic==2.7.4`

### 2. Cập nhật cấu hình khởi chạy trong [app.py](file:///d:/baihoc/Pet%20project/tracking/app.py) [MODIFY]
Thay đổi cách uvicorn khởi chạy để tự động nhận cấu hình cổng và host động được cấp phát bởi các nền tảng đám mây:
```python
if __name__ == "__main__":
    import uvicorn
    # Đọc host và port từ biến môi trường (phục vụ deploy cloud)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
```

### 3. Tạo tệp [.python-version](file:///d:/baihoc/Pet%20project/tracking/.python-version) [NEW]
Chỉ định rõ phiên bản Python là `3.11.9`.
* **Lý do:** Mặc định Render tự động chọn phiên bản Python mới nhất (ở đây là Python 3.14). Do Python 3.14 quá mới nên chưa có gói nhị phân dựng sẵn (wheel) cho `pydantic-core`, buộc pip phải biên dịch từ mã nguồn (Rust/Maturin) trong quá trình cài đặt. Khi đó, trình cài đặt cố gắng ghi cache vào thư mục hệ thống `/usr/local/cargo/registry/cache` và bị lỗi quyền ghi (`Read-only file system`). Việc ghim phiên bản Python `3.11.9` giúp Render sử dụng trực tiếp bản build sẵn có một cách trơn tru và an toàn.

---

## 🧪 Kết Quả Kiểm Thử Nội Bộ

1. **Chạy các Test Cases thuật toán (`test_matching.py`):**
   * Đã chạy thành công, toàn bộ 3 bài kiểm thử (Forced Match, Hard Constraints, Rejection & Rematching) đều vượt qua mà không phát sinh lỗi thuật toán.
2. **Khởi chạy ứng dụng Web Server nội bộ:**
   * Thử nghiệm chạy cục bộ cho thấy server khởi chạy thành công trên host `0.0.0.0` và cổng `8000`.

---

## 🚀 Hướng Dẫn Các Bước Tiếp Theo Để Deploy Lên Render (Miễn Phí)

Để đưa ứng dụng lên chạy chính thức và lấy URL gửi cho người ngoài Hà Nội test, bạn chỉ cần thực hiện 4 bước đơn giản sau:

### Bước 1: Đẩy code mới lên GitHub
Mở Git Bash hoặc Terminal tại thư mục của dự án và chạy các lệnh:
```bash
git add requirements.txt app.py .python-version
git commit -m "Configure app and pin Python version for cloud deployment"
git push origin main
```
*(Nếu bạn chưa kết nối với repository GitHub của mình, hãy tạo một repo trống trên GitHub rồi push code lên nhé).*

### Bước 2: Đăng nhập vào Render
1. Truy cập trang web [Render.com](https://render.com/).
2. Nhấp vào **Sign Up** và chọn đăng nhập bằng tài khoản **GitHub** của bạn.

### Bước 3: Tạo một Web Service mới
1. Trên trang Dashboard của Render, nhấn nút **New +** ở góc trên bên phải -> Chọn **Web Service**.
2. Chọn repo GitHub chứa dự án `tracking` của bạn từ danh sách hiển thị và nhấn **Connect**.
3. Điền cấu hình cho Web Service như sau:
   * **Name:** `matching-system` (hoặc tên bất kỳ bạn thích).
   * **Region:** Chọn khu vực gần Việt Nam nhất (ví dụ: `Singapore`).
   * **Branch:** `main` (hoặc nhánh chứa code của bạn).
   * **Language:** `Python`.
   * **Build Command:** `pip install -r requirements.txt`.
   * **Start Command:** `python app.py` (hoặc `uvicorn app:app --host 0.0.0.0 --port $PORT`).
   * **Instance Type:** Chọn gói **Free** (Miễn phí).

### Bước 4: Nhấn Deploy và nhận liên kết
1. Nhấp vào nút **Create Web Service** ở cuối trang.
2. Render sẽ tự động tải mã nguồn, cài đặt các thư viện trong `requirements.txt` và khởi chạy server.
3. Khi trạng thái chuyển sang màu xanh lá **"Live"**, bạn sẽ thấy một đường link công khai ở góc trên bên trái màn hình (ví dụ: `https://matching-system.onrender.com`).
4. **Chia sẻ link này cho bất kỳ ai** ở ngoài Hà Nội để họ bắt đầu thử nghiệm hệ thống.
