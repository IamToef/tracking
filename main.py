import os
import sys
import threading
import time
import webbrowser

# Thêm thư mục backend vào sys.path để các import trong app.py hoạt động bình thường
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.append(backend_dir)

def open_browser(url):
    # Đợi server uvicorn khởi động xong trong 1.5 giây trước khi mở trình duyệt
    time.sleep(1.5)
    print(f"🌍 Tự động mở trình duyệt tại: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    import uvicorn
    # Khởi chạy uvicorn trỏ vào file app trong thư mục backend
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    url = f"http://{host}:{port}"

    # Chạy luồng phụ để mở trình duyệt tự động
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Sử dụng chuỗi định dạng để reload hoạt động chính xác
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)
