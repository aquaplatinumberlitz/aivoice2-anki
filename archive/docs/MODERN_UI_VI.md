# Giao diện quản lý 0.2.0

> Hồ sơ lịch sử trước 0.3.0. Source/backend và tool cũ được tra tại tag v0.2.0; hướng dẫn hiện hành ở [docs/README](../../docs/README.md).

Giao diện mới dùng Qt 6 (ưu tiên PySide6, hỗ trợ PyQt6), thay phần Tkinter.
Source ở `src/setup/desktop_ui.py`, binding adapter ở `qt_compat.py`; nghiệp
vụ cài đặt/quản lý giọng vẫn ở install_core/voice_manager/integrations.
Backend worker/HTTP không phụ thuộc Qt, vẫn dùng được khi GUI đã đóng.

Ảnh tham khảo: [cài đặt hoàn tất](../notes/evidence/modern-ui/setup-wizard-complete.png),
[nghe thử](../notes/evidence/modern-ui/preview-dialog.png).

## Các luồng chính

- **Cài đặt mới:** nguồn MSI/Voice/Lang và nơi cài trong biểu mẫu gọn, bảng
  giọng có tìm kiếm/lọc, chọn/bỏ chọn các dòng đang lọc. Danh sách giọng
  cuộn trong bảng, không kéo dài toàn bộ cửa sổ. Nút cài ở thanh dưới cùng.
- **Quản lý giọng:** chọn bản cài rồi dùng Thêm giọng… để mở hộp thoại nguồn
  riêng. Giọng đã cài được đánh dấu và không cho chọn lại. Gỡ một dòng giọng,
  hoặc khôi phục từ danh sách backup có tên giọng/thời điểm rõ ràng.
- **Nghe thử:** chọn giọng và câu mẫu, tạo WAV rồi phát. Dừng ngăn phát kết
  quả đang chờ; đổi câu/giọng bỏ kết quả cũ. Có Phát lại và Mở file WAV.
- **Hỗ trợ:** kiểm hash file hoặc lưu support ZIP metadata, không upload.

Hộp chọn thư mục dùng QFileDialog của Qt và giao diện hệ thống khi desktop
cung cấp native integration; hỗ trợ dán path, nhớ thư mục đã chọn. Có thể
chọn Voice/voicebanks hoặc thư mục cha chứa chúng. Lang được tìm cạnh nguồn.

Progress theo **giai đoạn**, không giả là phần trăm thời gian còn lại:
kiểm input → trích MSI → chép dữ liệu (tính byte file đã chép) → patch →
chuẩn bị prefix → tổng hợp kiểm tra → kết nối ứng dụng. Chỉ thành công mới
đạt 100%; lỗi giữ mốc đã đạt và đưa thông báo/chi tiết để xử lý. Tác vụ mới
bắt đầu lại từ 0. Khởi tạo không tự phát demo; nút Nghe thử là thao tác riêng.

## Phụ thuộc và âm thanh

Máy chạy trình quản lý cần PySide6 hoặc PyQt6 cho Python hệ thống. Một số
bản Anki tự mang Python/Qt riêng, nên chỉ cài Anki chưa chắc đã cung cấp
module Qt cho trình quản lý. Khách không cần compiler/.NET SDK để dùng.
Thiếu Qt được báo qua KDialog/Zenity nếu có, đồng thời in thông báo cho dev.

Nghe thử ưu tiên Qt Multimedia, dùng QMediaPlayer và thiết bị âm thanh mặc
định. Nếu module Multimedia thiếu, dùng mpv khi có; nếu không có trình phát,
WAV vẫn được giữ để mở bằng ứng dụng hệ thống. Tạo WAV thành công và player
nhận yêu cầu không đồng nghĩa đã được người dùng nghe xác nhận trên loa.

Khi dịch vụ của đúng instance đã chạy, demo gọi HTTP của instance đó. Nếu
chưa chạy, demo dùng worker tạm rồi đóng worker sau khi tạo WAV. Không cần
mở Editor. Lock quản lý giọng vẫn chặn thay dữ liệu trong lúc engine dùng.

## Kiểm chứng

Unit Qt kiểm bảng lọc/chọn, nguồn thêm giọng độc lập, dialog desktop/history,
launch Anki/Editor tách biệt, tiến độ thành công 100%/lỗi không 100%, bỏ audio
trả muộn khi text đổi. Bài cài sạch kiểm cả wizard Qt → 100% → tạo WAV demo
và gọi player → thêm/gỡ/khôi phục giọng → pipeline Anki mới/cũ.

Anki smoke trong namespace không có sound device dùng MPV null sink qua
mpv.conf **chỉ trong base profile thử**, đồng thời dừng queue trước khi
đóng. Không đổi cấu hình player của khách. Cách này kiểm đường WAV/player
và tránh MPV treo lúc thoát do thiếu ALSA device; không chứng minh nghe loa.
Các cửa sổ editor do harness tự tạo được cleanup/deleteLater trước khi
đóng Anki, tránh để webview sống tới lúc Python/Qt hủy ứng dụng. Đây là
quy tắc vòng đời của công cụ test, không phải thay đổi collection của khách.

Các quyết định bỏ qua nghiệm thu máy/loa thật và hoãn updater/uninstall từ
đợt trước vẫn giữ nguyên. vntext chưa được triển khai trong đợt giao diện.
