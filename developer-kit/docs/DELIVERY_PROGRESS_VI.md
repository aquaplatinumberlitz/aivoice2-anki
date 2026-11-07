# Tiến độ bàn giao — 2026-11-06

## Giao diện 0.2.0

Đã chuyển manager sang Qt 6 với điều hướng bên trái, bảng giọng có tìm
kiếm/lọc và vùng progress/thao tác cố định. Thêm giọng có hộp thoại nguồn
riêng; sau cài có nút mở Anki/Editor/nghe thử. Progress kết thúc ở 100% khi
thành công. Demo tạo WAV và phát qua Qt Multimedia (mpv dự phòng), có
chọn giọng/câu, dừng/phát lại/mở WAV và chống phát kết quả cũ.

Đã kiểm wizard Qt trên prefix sạch: cài riêng Aoi, 100%, mở hộp thêm giọng,
demo WAV/player, quản lý giọng và pipeline Anki hai editor đều đạt. Không
tuyên bố đã nghe xác nhận loa thật trong namespace. Chi tiết:
[MODERN_UI_VI.md](MODERN_UI_VI.md).

## Bản sửa 0.1.1 — quét voicebank từ nguồn chọn

Installer không còn giới hạn bốn giọng trong baseline. Nguồn `Voice/` thực
tế được quét, hỗ trợ metadata `info.bin`/`infox.bin`; mọi Akane tự dùng Kansai,
các giọng khác tự dùng Standard theo quy tắc người phát hành xác nhận. Cả cài mới/thêm/gỡ/khôi phục dùng cùng cơ chế
import và ghi hash nguồn trong `voice-imports.json`. Giữ nguyên guard MSI/GUI.

Đã quét đủ 28 thư mục ở nguồn được báo lỗi và xác nhận giao diện có 28
dòng chọn giọng, không yêu cầu tự chọn dialect. Kiểm thử cô lập cài `KizunaAkari_ns_48` dùng Standard tự động và `akane_west_emo_48` tự điền Kansai: tổng hợp, gỡ và khôi phục đều đạt.
Không suy từ đó rằng mọi giọng trong nguồn đều đã qua tổng hợp. Bước khởi
tạo nay kiểm từng giọng và báo lỗi tương thích của giọng cụ thể.

Đã chốt bàn giao 0.1.0 Linux x86-64 cho pipeline Anki theo duyệt ngày
2026-11-06. vntext chỉ lưu roadmap, chưa triển khai. Không suy từ quyết
định duyệt rằng mọi máy/distro đã được chứng nhận.

## Đã triển khai

- Baseline 344 file: MSI stock (326), hai Lang và 16 file của bốn NV công ty
  cấp. Không đưa bank legacy từ bản cài cá nhân vào dữ liệu bàn giao.
- Một app/Voice/Lang cho GUI và backend; config version 1, đường dẫn tương
  đối/XDG, prefix riêng, registry dialect và drive alias cho đường dẫn có dấu.
- Worker/helper/addon build trước; backend không tự chạy compiler. GUI giữ
  framework stock, helper .3 và UI patch Deactivate đã kiểm chứng.
- Wizard cài mới: chọn MSI/Lang/voicebanks/giọng, verify hash, staging,
  commit không ghi đè root tồn tại, backup stock, init prefix và synth mẫu.
- Quản lý thêm/gỡ/khôi phục giọng; giữ tối thiểu một giọng, fallback default,
  kiểm hash backup. Shared/exclusive lock chặn thay dictionary đang dùng.
- Service/shortcut theo instance, chọn cổng không trùng dịch vụ khác, kiểm
  health đúng instance. Cài addon giữ field/settings cũ và addon khác.
- CLI diagnose/verify-files/support ZIP metadata, không xuất log thô hoặc
  collection/câu/audio/license cá nhân. Có docs khách, runbook, build, RE index.
- Tool/source nghiên cứu độc nhất đã được giữ ở src/research có provenance.

## Bằng chứng kiểm tra

- 23 unit tests về config, transaction, symlink/path, backup, lock, bảo toàn
  addon và support redaction đã pass.
- Wine/offline namespace: hai prefix mới, không thấy home/prefix cá nhân,
  path có dấu/khoảng trắng. Bốn WAV です。 khớp PCM baseline; đổi dialect,
  cache và GUI cùng chạy được.
- Anki toàn tuyến trên NewEditor và Editor legacy: chọn こんにちは → mic →
  preview WAV → xác nhận chèn đúng byte vào media, không trùng tag, giữ các
  field khác. Preview không tự sửa note/media. Đổi câu khi chờ TTS bỏ kết quả cũ,
  không phát audio trả về trễ.
- Voice lifecycle: thêm bank chưa đăng ký bị loại khỏi danh sách; đăng ký
  dialect thì synth đúng. Gỡ default Akane chuyển Aoi; GUI chỉ còn ba thẻ.
  Thiếu voice.lic bị phát hiện, khôi phục trả lại PCM đúng.
- Cài từ MSI riêng qua wizard trong namespace: chỉ Aoi/standard → thêm
  Akane/Kansai → gỡ/khôi phục → chặn gỡ khi engine chạy → tích hợp addon và
  toàn tuyến Anki mới/cũ. Không lấy app từ prefix cá nhân.
- Service thật: unit thử độc lập tự chọn cổng 17863, health đúng instance
  và trả đúng Aoi; đã dọn unit/prefix thử, service cũ 17862 vẫn hoạt động.

Evidence: [P1](../notes/evidence/delivery-p1/result.json),
[voice lifecycle](../notes/evidence/voice-lifecycle/result.json),
[wizard/Anki](../notes/evidence/setup-clean/result.json),
[service](../notes/evidence/service-activation/result.json).

Hai lỗi môi trường/thời điểm đã được phát hiện và sửa khi kiểm thử: Xvfb
chọn NVIDIA (ép Mesa trong test), và wineboot trả về trước khi flush registry
(prefix mới được shutdown/wait trước khi đặt alias). Không patch thêm engine.

## Giới hạn đã được chấp nhận trong đợt bàn giao

- Bản candidate trước đã kiểm từ archive; kiểm lại cùng source/payload sau
  thay đổi cuối và giữ report cạnh archive để tránh lệch bản kiểm/bản giao.
- Máy/VM khách thứ hai, ma trận distro/Wine/dependency, loa thật và reboot.
  Xvfb/Anki player hook không thay xác nhận nghe qua thiết bị vật lý.
- Update toàn bộ MSI, uninstall tích hợp, import giọng ZIP, hồi quy mất điện/
  transaction recovery rộng hơn; candidate hiện dùng folder và root mới.
- Review UX các menu license cũ và bài thực hành dev newbie theo tài liệu.

Người dùng đã yêu cầu không test thêm các mục máy khách/loa thật và cho
qua phần hoàn thiện update/uninstall ở đợt này. Ghi nhận tại
[user-acceptance.json](../release/user-acceptance.json). Không triển khai
updater/uninstaller bổ sung hoặc chuyển sang vntext trong lượt chốt gói.

Service/Anki cá nhân hiện tại không được chuyển sang candidate trong lúc
nghiên cứu; bản cũ vẫn giữ chín giọng. Các thao tác khách dùng qua manager
sẽ áp dụng trên root riêng được chọn. Bản đóng gói không chứa activation,
Wine prefix, collection hoặc audio cache của tác giả.
