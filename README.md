# Hướng Dẫn Vận Hành Hệ Thống Đối Sánh Mentor-Student 🚀

Hệ thống đối sánh tự động phân bổ Học sinh THCS (Grades 7-9) cho Cố vấn phù hợp dựa trên các điều kiện ràng buộc cứng về Lịch học và Giới tính yêu cầu, đồng thời tối ưu hóa độ tương hợp hai chiều (kỳ vọng của phụ huynh vs kỹ năng của cố vấn).

---

## 📂 Các File Dự Án Chính

- `matching_engine.py`: Chứa toàn bộ thuật toán đối sánh chính (sử dụng Heuristic MRV để xếp lịch, tính điểm tương tích theo Jaccard & Thematic, mô phỏng từ chối Q4).
- `app.py`: Server API FastAPI kết hợp phục vụ giao diện Dashboard.
- `index.html`, `style.css`, `script.js`: Giao diện Dashboard tối ưu (Glassmorphism Dark Theme).
- `overrides.json`: File cấu hình lưu trữ các tùy chọn ghi đè (Ghép đôi cưỡng ép, Chặn ghép, Bỏ qua thành viên).
- `test_matching.py`: Script chạy kiểm thử tự động thuật toán đối sánh.
- `../n8n/mentor_student_matching_workflow.json`: File cấu hình import vào n8n để tích hợp workflow tự động.

---

## 🛠️ Hướng Dẫn Chạy Hệ Thống

### 1. Khởi động Web Dashboard & API Server
Hệ thống sử dụng Python 3 có sẵn trong môi trường ảo `Car_db\venv` để chạy server.
Chạy lệnh sau trong PowerShell hoặc Terminal:
```powershell
& "D:\baihoc\Pet project\Car_db\venv\Scripts\python.exe" "d:\baihoc\Pet project\tracking\app.py"
```
Server sẽ được kích hoạt tại: **`http://127.0.0.1:8000`**

### 2. Sử dụng Hệ thống trên Trình duyệt
Mở trình duyệt web của bạn và truy cập địa chỉ: **`http://127.0.0.1:8000`**

Giao diện sẽ hiển thị:
- **Thanh cấu hình bên trái:** Điều chỉnh thời lượng buổi học, độ ưu tiên giới tính, trọng số điểm và nhấn **"Chạy đối sánh"** để cập nhật kết quả.
- **Tab Ghép cặp:** Chi tiết lý do và thông tin các cặp đã ghép. Mọi cặp ghép có điểm tương hợp dưới ngưỡng quy định sẽ được cảnh báo đỏ (Poor Fit).
- **Tab Chưa ghép:** Báo cáo chi tiết danh sách học sinh không thể xếp lớp và lý do lỗi (Kín lịch, Sai giới tính, hoặc Không có lịch trùng).
- **Tab Quản lý Ghi đè (Overrides):** Thêm hoặc xóa các ghi đè để điều chỉnh thuật toán xếp lớp mà không cần sửa code.
- **Tab Mô phỏng Từ chối:** Nhấn nút **"Mô phỏng từ chối (20%)"** ở thanh bên trái để chạy mô phỏng từ chối (Q4) và xem báo cáo so sánh trước/sau khi thay đổi.

---

## 📈 Kiểm Thử Thuật Toán
Để chạy kiểm thử tự động thuật toán đối sánh độc lập và xác minh các điều kiện ràng buộc giới tính & lịch học:
```powershell
& "D:\baihoc\Pet project\Car_db\venv\Scripts\python.exe" "d:\baihoc\Pet project\tracking\test_matching.py"
```
Các kiểm thử sẽ tự động chạy và in ra báo cáo thống kê mức độ khớp và kiểm tra 100% không trùng lặp lịch & đúng giới tính.
