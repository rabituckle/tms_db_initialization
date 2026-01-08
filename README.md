# Ride-Hailing Database – Mock Data Generator

## 📌 Mục tiêu
Sinh dữ liệu giả (mock data) cho hệ thống ride-hailing
để phục vụ:
- test database
- demo hệ thống
- báo cáo môn học

## 📂 Cấu trúc
- `generators/` : sinh dữ liệu (.sql)
- `tests/`      : kiểm tra dữ liệu bằng pytest
- `data/`       : file output .sql
- `config.py`   : cấu hình số lượng & seed
- `run_all.py`  : chạy toàn bộ pipeline

## ▶️ Cách chạy
```bash
python run_all.py
python -m pytest
