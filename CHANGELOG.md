# 0.3.1 — hướng dẫn cài từ đầu và phân chia source

- Một Quickstart A–Z: tải đúng gói, dependency theo distro, ảnh wizard,
  kiểm URL qua Anki/browser, nghe Anki và vntext; không build backend.
- README ba repo dẫn thẳng về cùng Quickstart; tài liệu kỹ thuật đọc riêng.
- Chuyển source addon/helper về src; chuyển developer-kit lịch sử về archive.
- Runtime/backend và addon được đóng gói giữ nguyên phiên bản đã kiểm chứng.

# 0.3.0 — backend chung mặc định

- start-setup.sh và payload dùng aivoice2api 0.1.0 theo lock: WAV/PCM stream,
  warm/prepare/cancel, quota WAV 512 MiB/7 ngày.
- Gỡ daemon WAV cũ, bản sao setup và tool build worker cũ khỏi main.
- Manager dùng cùng runtime với service; sửa synth/preview theo kết quả mới.
- Test installer chuyển về tests; thêm quy trình checksum/archive hiện hành.
- Bản 0.2.0 còn trong tag v0.2.0; hồ sơ RE giữ lại và dẫn về source đúng phiên bản.
- Không thay đổi native engine/GUI patch hoặc phạm vi QA đã được ghi nhận.

# Changelog

## 0.2.0 — 2026-11-06

- Giao diện Qt 6 mới, điều hướng bên trái và bảng giọng có tìm kiếm/lọc.
- Thêm giọng mở hộp thoại chọn nguồn riêng, tự bỏ chọn giọng đã cài.
- Hộp chọn file/thư mục của Qt/desktop, nhớ thư mục đã chọn và nhận cả
  thư mục cha chứa Voice hoặc voicebanks.
- Tiến độ theo giai đoạn, kết thúc 100% khi thành công; lỗi giữ tiến độ đã đạt.
- Nút mở Anki, Editor và nghe thử luôn dễ tìm sau cài đặt.
- Nghe thử chọn giọng/câu, tạo WAV và phát âm thanh; có dừng/phát lại/mở WAV.
- GUI dùng PySide6 hoặc PyQt6; backend không cần Qt và vẫn chạy headless.

## 0.1.1 — 2026-11-06

- Quét thư mục Voice/voicebanks được chọn, bỏ giới hạn danh sách bốn giọng.
- Giọng mới ngoài danh sách đã biết vẫn hiện; tự chọn Kansai cho mọi Akane,
  Standard cho giọng còn lại theo quy tắc người phát hành; ghi hash nguồn
  và tự đăng ký vào runtime.
- Cài mới và thêm/gỡ/khôi phục đều hỗ trợ giọng được import. Giữ guard
  phiên bản MSI/GUI, không dùng hash của bốn giọng cũ để chặn bank mới.
- Bước khởi tạo thử tổng hợp từng giọng đã cài và báo giọng lỗi tương thích.

## 0.1.0 — 2026-11-06

- Manifest stock MSI 2.14.1 và bốn NV công ty cấp, Lang tách khỏi MSI.
- Một app/Voice/Lang cho GUI và backend, config portable và registry dialect.
- Helper FreeLicenseManager stock framework, nhãn Full version, UI ẩn/chặn Deactivate.
- Backend worker build sẵn, HTTP loopback; addon chọn câu, preview và chèn có xác nhận.
- Trình thiết lập ban đầu, staging/hash/backup; quản lý thêm/gỡ/khôi phục giọng.
- Service/shortcut theo instance, cài addon giữ cấu hình, support ZIP metadata.
- Source/dev-kit, báo cáo RE và tool nghiên cứu có provenance.

Đã được người dùng duyệt bàn giao, bỏ qua QA máy độc lập/loa thật và hoãn
hoàn thiện update/uninstall trong đợt này. Không đồng nghĩa đã chứng nhận
mọi distro/GUI feature hoặc Windows native.
vntext chỉ là roadmap sau khi pipeline Anki hoàn tất.
