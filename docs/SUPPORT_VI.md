# Hỗ trợ theo kiến trúc mới

Bắt đầu từ version addon, backend manifest/lock và root thực sự khách dùng.
Lock repo là phiên bản đóng gói/QA; bản cài có thể chưa được nâng lên lock đó.
Không kết luận chỉ từ tên thư mục hoặc cổng mặc định.

1. Đọc runtime.json/integration.json, xác định URL và service đúng instance.
2. Theo [CONNECT_VI](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/CONNECT_VI.md),
   chạy diagnose/verify-files/health/voices và câu WAV tổng hợp ngoài client.
3. WAV lỗi hoặc voice/dialect sai: xử lý ở backend/data/registry; không
   sửa addon hoặc pitch để giả hai giọng khác nhau.
4. WAV đúng, Anki lỗi: kiểm api_url, editor/selection và field/media theo
   [ADDON_VI](ADDON_VI.md). WAV đúng nhưng vntext lỗi: dùng runbook vntext.
5. Voicebank thêm/gỡ qua manager đúng instance: lưu/đóng Editor, dừng
   service, thao tác có backup/manifest, bật lại và Refresh hai client.

Backend code/config/worker thuộc aivoice2api; addon/setup/GUI patch thuộc
repo Anki; extraction/overlay/player thuộc vntext. Ghi issue đúng repo,
kèm version, hash, kết quả metadata và bước tái hiện dùng câu tổng hợp.
Không gửi raw license, activation, collection, log hàng loạt thoại hoặc key.

## Quản lý và rollback

Manager từ setup compose tương thích backend mới; snapshot manager 0.2.0
có chỗ giả định Engine.speak chỉ trả 2 phần tử. Nếu gặp lỗi unpack khi demo
hoặc initialize, dùng manager đã compose, không patch worker để chữa UI.
Giữ nguyên API WAV giúp addon 0.2.0 tiếp tục dùng được backend mới.

Nâng backend có backup đồng bộ server/worker/support/manifest và receipt;
xem mục 8 guide chung. Lùi addon: đóng Anki, backup addon hiện tại rồi khôi
phục bản đã biết tốt, giữ collection/media/settings. Lùi GUI helper/UI là
công việc riêng, phải theo baseline/evidence cùng bộ, không trộn snapshot.

`release/user-acceptance.json` ghi việc được duyệt bỏ qua ở bundle cũ.
Những mục đó không phải test đã pass; chưa có updater/uninstall hoàn chỉnh.
[ARCHIVE_INDEX_VI](ARCHIVE_INDEX_VI.md) dẫn tới runbook/build/RE lịch sử và
các giới hạn khi dùng probe; không chạy tool nghiên cứu lên prefix khách.
