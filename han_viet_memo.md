# Quy trình xử lý han_viet_dich-xong

## Tìm và gom cụm Hán-Việt khó hiểu

1. Chạy grep lấy câu chứa cụm cần xử lý

   ```bash
   rg -H -n 'xạ ngũ ác|uất thập ma môn|khả tuyến|giao đàm|chưởng quy|hòa ly|bản sự|hướng ta' dich-xong > raw_grep_output.txt
   ```

2. Chuyển grep thành JSON khóa/giá trị

   ```bash
   uv run convert_grep_to_json.py raw_grep_output.txt han_viet_kho_hieu.json
   ```

   - `convert_grep_to_json.py` đọc các dòng có dạng `"id": "text"` từ raw_grep_output.txt.

## Dịch và áp dụng

1. Mở `han_viet_kho_hieu.json` để tham chiếu, dịch thủ công sang `han_viet_dich-xong.json`.
2. Chạy script áp dụng vào toàn bộ thư mục `./dich-xong`:

   ```bash
   uv run scripts/apply_han_viet_dich_xong.py --map ./han_viet_dich-xong.json --dir ./dich-xong
   ```

   - Tạo backup tại `./dich-xong/_backup_<timestamp>`.
   - `total_updates` cho biết số thay thế.

## Lưu ý

- Script thử nhiều encoding (utf-8, gb18030, gbk, latin-1) khi đọc JSON.
- Chỉ xử lý file `.json` (bỏ qua file ẩn, `._*`).
- Nếu muốn dry-run, sửa script để hỗ trợ hoặc tự log diff trước khi commit.

## Tập tin liên quan

- `convert_grep_to_json.py`
- `scripts/apply_han_viet_dich_xong.py`
- `han_viet_kho_hieu.json`
- `han_viet_dich-xong.json`
