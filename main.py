import os
import sys

# Thêm thư mục backend vào sys.path để các import trong app.py hoạt động bình thường
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.append(backend_dir)

if __name__ == "__main__":
    import uvicorn
    # Khởi chạy uvicorn trỏ vào file app trong thư mục backend
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    # Sử dụng chuỗi định dạng để reload hoạt động chính xác
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)
