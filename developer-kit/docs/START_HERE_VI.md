# A.I.VOICE2 + Anki — bắt đầu sử dụng

**Bản bàn giao 0.2.0 Linux x86-64, giao diện Qt mới trên nền 0.1.0 đã duyệt.**
Người dùng đã duyệt bỏ qua nghiệm thu máy khách/loa thật và hoãn hoàn thiện
updater/uninstall trong đợt này. Phạm vi Windows chưa được chứng nhận.
Bộ cài gốc, Lang và giọng được cung cấp
riêng; bộ tích hợp không mang license cá nhân hoặc Wine prefix của tác giả.

## Chuẩn bị

- A.I.VOICE2 Editor MSI 2.14.1 đúng bản được hỗ trợ.
- Thư mục `Lang/` gồm standard/Kansai và `voicebanks/` do bên bàn giao cấp.
  MSI Editor không chứa các dữ liệu này.
- Linux có Python 3 + Qt 6 (PySide6 hoặc PyQt6), Wine, công cụ `msiextract` (thường thuộc gói
  msitools). Anki Desktop cần có nếu muốn dùng addon. Trình thiết lập báo
  thiếu dependency; bản này chưa tự cài gói hệ thống cho mọi distro.
- Nghe thử dùng Qt Multimedia khi có (hoặc mpv dự phòng). Nếu trình phát
  thiếu hoặc sound device lỗi, vẫn có thể mở WAV đã tạo để kiểm tra.
- Không cần compiler, .NET SDK, IDA hoặc REA để dùng bản runtime.

## Cài lần đầu

1. Giải nén bộ tích hợp vào thư mục của bạn. Mở `start-setup.sh`; nếu trình
   quản lý file hỏi, chọn chạy chương trình. Trên hệ thống không cho chạy
   script bằng double-click, dev hỗ trợ có thể mở bằng `bash start-setup.sh`.
2. Chọn `AIVoice2Editor.msi`. Nếu Lang/voicebanks nằm cạnh MSI, công cụ tự
   điền; nếu không, chọn hai thư mục đó riêng.
3. Dùng tìm kiếm/bộ lọc trong bảng, đánh dấu giọng muốn dùng và chọn thư
   mục **mới** để cài. Danh sách cuộn riêng trong bảng. Công cụ
   không ghi đè thư mục đã tồn tại hoặc tự sửa bản A.I.VOICE2 cá nhân.
4. Chọn tạo shortcut/backend. Nếu có Anki, chọn kết nối Anki và đóng Anki
   trước khi cài. Mặc định native Linux dùng `~/.local/share/Anki2/addons21`;
   bản portable/custom cần chọn đúng `addons21`. Flatpak chưa được chứng nhận.
5. Bấm **Cài đặt và kiểm tra**. Công cụ kiểm tra input, dựng bản sạch, chép
   giọng vào app/Voice, áp patch đúng phiên bản, tạo prefix và tổng hợp mẫu.
6. Thanh tiến độ dừng ở **100%** khi hoàn tất. Nút **Mở Anki**, **Mở
   A.I.VOICE2**, **Nghe thử…** nằm ở thanh dưới cùng. Có shortcut **Quản lý
   A.I.VOICE2 + Anki** để bảo trì bản cài.

Trong ứng dụng, `app/Voice/` là nơi lưu giọng duy nhất; GUI và backend cùng
đọc. GUI và engine dùng hai prefix riêng để không tranh cài đặt. Các file
`.lic` runtime đi kèm vẫn được giữ; khách không phải nhập activation key cá nhân.

## Dùng trong Anki

1. Chọn note type **A.I.VOICE2 · Nhật–Việt** hoặc dùng note type hiện có.
2. Nhập tiếng Nhật, romaji, nghĩa Việt; bộ này chưa tự dịch hoặc sinh romaji.
3. Bôi đen câu tiếng Nhật và bấm mic. Chọn giọng, nghe thử.
4. Nếu đồng ý, bấm **Đồng ý · Chèn vào card**. WAV được lưu vào media, tag
   sound được thêm vào field đích. Preview/đóng hộp thoại không sửa note.

Backend chạy nền, không cần mở Editor. Audio đã chèn được sync như media
Anki thông thường; chức năng mic/addon thuộc Anki Desktop.

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

## Khi cần hỗ trợ

Trong Hỗ trợ, bấm **Lưu báo cáo hỗ trợ…**. ZIP chứa metadata và kết quả
kiểm tra file/config, đường dẫn chính được ẩn. Không tự gửi file ra ngoài.
Không chứa collection Anki, audio/câu học, raw license, activation hay log thô.

Dev hỗ trợ bắt đầu tại [DEV_HANDOVER_INDEX_VI.md](DEV_HANDOVER_INDEX_VI.md),
sau đó dùng [SUPPORT_RUNBOOK_VI.md](SUPPORT_RUNBOOK_VI.md).
vntext là kế hoạch sau; phiên bản này tập trung pipeline Anki.

Quyết định nghiệm thu nằm trong `release/user-acceptance.json`. Các mục đã
duyệt bỏ qua không được tính là test đã pass hoặc chức năng đã triển khai.
