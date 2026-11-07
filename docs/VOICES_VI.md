# Quản lý giọng sau khi cài

Cài mới: [Quickstart](QUICKSTART_VI.md). Bảo trì đúng root đã cài;
GUI và backend cùng đọc app/Voice và app/Lang trong root đó.

## Thêm, gỡ và khôi phục giọng

1. Lưu/đóng Editor. Mở shortcut Quản lý, vào **Quản lý giọng**, chọn đúng thư mục bản cài.
2. Bấm **Dừng dịch vụ** nếu đang chạy service của bản này.
3. Bấm **Thêm giọng…** để mở hộp thoại riêng: chọn nguồn, chọn giọng trong
   bảng rồi bấm **Thêm giọng đã chọn**. Không cần quay về Cài đặt mới.
   Giọng đã cài được đánh dấu và không cho chọn để tránh chép đè.
4. Gỡ: chọn giọng đã cài và bấm Gỡ. Giọng chuyển sang backup; không xóa
   audio đã lưu trong card. Luôn giữ ít nhất một giọng; default bị gỡ sẽ
   chuyển sang giọng còn lại.
5. Bấm **Khôi phục giọng…** rồi chọn bản dự phòng có sẵn. Công cụ kiểm tra
   hash trước khi khôi phục.
6. Bấm **Nghe thử…**, **Bật dịch vụ**, mở lại Editor và Refresh danh
   sách trong addon Anki.

Danh sách giọng được quét từ thư mục bạn chọn, không cố định bốn hay 28 giọng.
Mỗi giọng cần .aivdic, voice.lic, images.dat và info.bin hoặc infox.bin.
Giọng thiếu file vẫn được liệt kê kèm lý do nhưng không cho cài. Ngôn ngữ được tự chọn theo quy tắc người phát hành: mọi giọng Akane dùng
Kansai, các giọng còn lại dùng Standard, kể cả bank mới chưa từng thấy.
Khách không cần chọn dialect hoặc sửa source/baseline. Công cụ tự lưu
cấu hình ngôn ngữ và hash file nguồn. Khi khởi tạo, từng giọng được thử tổng hợp; gói
giọng mới có thể không tương thích engine 2.14.1 dù cấu trúc file hợp lệ.


Sau thêm/gỡ giọng, làm mới danh sách trong cả addon Anki và vntext.
Không cần dựng backend thứ hai hoặc xóa media đã chèn vào Anki.
