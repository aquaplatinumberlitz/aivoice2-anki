# Cập nhật, khôi phục và phạm vi hiện tại

> Hồ sơ lịch sử trước 0.3.0. Source/backend và tool cũ được tra tại tag v0.2.0; hướng dẫn hiện hành ở [docs/README](../../docs/README.md).

Đợt 0.1.0 được duyệt bàn giao với phạm vi bên dưới. Người dùng đã cho qua
phần hoàn thiện updater/uninstall; không coi các phần chưa có là đã triển khai.

Trước khi thay file: lưu/đóng Editor, đóng Anki nếu cập nhật addon, dừng
backend đúng instance. Dùng Quản lý hoặc service được ghi trong
`integration.json`; không kill wineserver của prefix cá nhân.

## Giọng

Gỡ giọng chuyển cả thư mục sang `backups/voices/<id>/`, kèm receipt/hash.
Không xóa Lang dùng chung hoặc audio Anki đã lưu. Khôi phục bằng tab Quản
lý; target đã tồn tại hoặc backup khác hash sẽ bị từ chối. Từ 0.1.1, manager
quét source và import giọng ngoài baseline; tự dùng Kansai cho Akane và
Standard cho các giọng còn lại.
Registry/hash được cập nhật tự động; thử synth khi khởi tạo để biết có
tương thích engine hay không.

## Helper và snapshot UI

Backup stock ở `backups/stock/ailm.dll` và `backups/stock/app.so`. Muốn lùi
patch GUI, đóng runtime rồi chép snapshot stock về `app/data/app.so`; GUI
cũ sẽ hiện lại Deactivate và có thể lỗi khi dùng caption Full version.
Khôi phục helper stock trả về luồng license GUI gốc, có thể gặp WMI trong
prefix sạch. Vì vậy rollback riêng từng file chỉ dùng để điều tra có chủ
đích; sản phẩm nên dùng cặp helper/UI đã QA cùng nhau.

Không áp patch của 2.14.1 vào app.so phiên bản khác. Không thay framework
stock bằng DLL sidecar cũ để chữa lỗi chung. Giữ binary gốc bất biến, build
candidate riêng và so manifest trước khi triển khai.

## Addon

Cài lại qua Quản lý khi Anki đã đóng; settings cũ trong meta.json được giữ,
endpoint được nối tới bản cài này. Backup addon trước đó nằm trong
`backups/integration/`. Nếu lùi addon, đóng Anki, chuyển bản hiện tại ra
ngoài addons21 rồi khôi phục thư mục `aivoice2_local` từ backup. Không xóa
collection hoặc media. Xác minh URL backend vẫn phù hợp sau rollback.

## Cài dang dở và giới hạn của candidate

- Lỗi trước commit: staging của tác vụ được dọn, source/app khác giữ nguyên.
- File đã commit nhưng prefix/native check lỗi: giữ bản cài và manifest để
  tiếp tục **Khởi tạo/kiểm tra** trong Quản lý; không ghi đè thư mục tồn tại.
- Không coi việc chạy setup lại vào cùng root là update toàn bộ engine.
  Trình nâng cấp toàn bộ phiên bản/MSI, uninstall tích hợp hoàn chỉnh, ZIP
  voice import và rollback tự động mọi sự cố mất điện chưa hoàn tất QA.
- Khi cần thử build mới trước khi updater hoàn thiện, cài vào root mới,
  kiểm nghiệm rồi chuyển tích hợp qua Quản lý. Giữ root cũ để khôi phục.

Chạy `verify-files` sau thao tác dev sửa tay để biết manifest có còn khớp;
không sửa hash manifest chỉ để che corruption. Xem runbook để lấy support ZIP.
