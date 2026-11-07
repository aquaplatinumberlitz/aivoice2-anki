# Runbook cho dev hỗ trợ mới

Đọc [ARCHITECTURE_VI.md](ARCHITECTURE_VI.md) trước. Làm trên bản cài được
quản lý hoặc bản thử; không sửa prefix/collection cá nhân để đoán lỗi.

## Bước kiểm tra ban đầu

Trong lệnh dưới, thay `/path/to/install` bằng thư mục bản cài:

```sh
python3 /path/to/install/runtime/runtime_cli.py --config /path/to/install/config/runtime.json diagnose
python3 /path/to/install/runtime/runtime_cli.py --config /path/to/install/config/runtime.json verify-files
```

`diagnose` chỉ đọc config/file/registry. `files_ready: true` chưa chứng minh
engine/player đã chạy. `verify-files` kiểm toàn bộ file có trong manifest;
`passed: true` nghĩa file còn khớp, không thay QA audio. Không in/đính kèm
raw `.lic` hoặc biến môi trường credential để hỗ trợ.

| Triệu chứng | Kiểm tra | Xử lý và kết quả mong đợi |
| --- | --- | --- |
| Setup báo sai MSI/payload | Baseline ID, hash input | Dùng đúng MSI 2.14.1 và payload cùng baseline; không bỏ version guard |
| Setup dừng sau cài file | transaction.json, log setup; prefix initialized | Tab Quản lý → Tiếp tục khởi tạo/kiểm tra; không cài đè thư mục tồn tại |
| GUI không mở | app/aivoice.exe, runtime.json, prefix GUI, logs/gui.log | Sửa cài đặt/prefix của đúng instance; không clone prefix cá nhân |
| GUI có giọng nhưng backend thiếu | app_dir của hai phía, registry, Lang/voice.lic | Đồng bộ config cùng app; khai báo dialect đã xác minh; Refresh Anki |
| Akane/Aoi giống nhau | Registry Akane=kansai, Aoi=standard; câu です。 | Chọn Lang đúng và kiểm hash PCM; không tạo khác biệt bằng pitch giả |
| こんにちは đọc sai | Text gửi API, encoding 0 trong worker, worker hash | Dùng UTF-8; build đúng worker; không tái dùng cache của worker lỗi |
| auth=-3/talker NULL | Engine/hash/prototype, engine runtime license | Theo POC_UNBLOCKED; không đoán tham số NULL hoặc xóa `.lic` |
| loadVoiceDic lỗi | Gói .aivdic + voice.lic của đúng bank | Giữ nguyên cả thư mục; kiểm manifest; giọng ngoài baseline cần xác minh riêng |
| Anki không kết nối | integration.json endpoint; healthz cùng instance | Bật service của instance, kết nối lại addon; không đổi URL ngẫu nhiên |
| Cổng bận | Unit cũ/instance khác; config port | Setup chọn port trống và cập nhật addon; không kill dịch vụ khác |
| Nghe preview sai câu | dialog text/audio_signature; cache worker hash | Sửa signature/UTF-8 trước; không chèn audio khi text/voice vừa đổi chưa synth lại |
| Chèn không được | Field đích, note/editor state, media writable | Test profile riêng và editor cũ/mới; giữ nguyên các field khác |
| Preview không có tiếng | Có WAV hợp lệ? Player có chạy? Thiết bị đầu ra? | Tách lỗi tổng hợp và sound device. ALSA/MPV fail trong namespace không chứng minh engine hỏng |
| Gỡ giọng bị chặn | GUI/worker giữ runtime lock | Lưu/đóng GUI, dừng backend instance rồi thao tác; bật backend lại sau |
| Giọng đã gỡ còn trong lựa chọn | Anki dialog/preset đang mở | Mở lại GUI/Refresh Anki; default tự chọn giọng còn lại; không xóa media cũ |
| Backup không restore | receipt/hash hoặc target giọng đã tồn tại | Không ghi đè; giữ backup để điều tra, chọn đúng instance/backup |
| Editor báo thiếu nid | Editor/NewEditor, bản addon | Cài addon có editor_compat; không thêm phụ thuộc editor.nid trở lại |

## Service và thông tin hỗ trợ

Tên unit nằm trong `integration.json`, dạng `aivoice2-local-<id>.service`.
Đọc log của **đúng unit**, không dùng tên service nghiên cứu cũ để đoán:

```sh
systemctl --user status aivoice2-local-INSTANCE.service
journalctl --user -u aivoice2-local-INSTANCE.service -n 50
```

Xem nội dung metadata trước khi export:

```sh
python3 /path/to/install/runtime/runtime_cli.py --config /path/to/install/config/runtime.json support-preview
python3 /path/to/install/runtime/runtime_cli.py --config /path/to/install/config/runtime.json --output ./support.zip export-support
```

ZIP mặc định chỉ có summary, không log/câu/audio/collection/activation. Nếu
cần log sâu hơn, dev và khách chọn nội dung cụ thể để kiểm tra/làm sạch;
không tự upload. File nguồn nghiên cứu còn nguyên trong workspace nội bộ.

## Khi cần RE thêm

Đọc [RE_FINDINGS_INDEX_VI.md](RE_FINDINGS_INDEX_VI.md), kiểm binary hash
trước khi dùng offset. Reproduce trên prefix sạch, lưu command/environment,
input hash, status/output và giới hạn kết luận. Một kết quả synth thành công
không xác nhận mọi menu GUI, mọi bank hoặc thiết bị âm thanh vật lý.
