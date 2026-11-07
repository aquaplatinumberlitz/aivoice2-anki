# Free client GUI review — 2026-11-06

**Đã sửa Deactivate:** patch UI `2.14.1-free-ui.1` ẩn nút cùng lời hướng
dẫn, callback cũ trả về ngay. Bốn thẻ giọng Full version và xuất WAV vẫn
hoạt động trong prefix sạch offline. Xem
[FREE_CLIENT_DEACTIVATION.md](FREE_CLIENT_DEACTIVATION.md).

**Helper .3:** nhãn hiển thị là **Full version** theo yêu cầu người dùng.
Helper .2 trước đó đã sửa danh sách trống tại Help → License Authentication →
License Confirmation. GUI ẩn mục có `activation_key` rỗng. Helper trả nhãn
không rỗng để hiện lại bốn voicebank, vẫn dùng manager miễn phí. Đã đối
chiếu chỉ đổi trường này, kiểm tra lại GUI offline và sau restart.
Ảnh trước/sau, trace và claim:
[license-list](evidence/free-client/license-list/README.md).

Hướng dẫn cơ chế và thao tác cho người mới:
[FREE_CLIENT_GUIDE_VI.md](FREE_CLIENT_GUIDE_VI.md).

Client thử dùng MSI 2.14.1 nguyên bản và Lang/bốn NV công ty cấp.
Thay **ailm.dll** bằng helper có source tại
[LicenseAdapter.cs](../../src/free-client/LicenseAdapter.cs); giữ nguyên
`AI.Framework.License.dll`, ailm.exe, engine và license runtime. Thêm
patch giao diện `data/app.so`, source [gui_patch.py](../../src/free-client/gui_patch.py);
patch này chỉ xử lý trang Deactivate, không cấp quyền engine.

Hiểu đơn giản: `ailm.exe` giữ nhiệm vụ khởi chạy, còn `ailm.dll` mới chọn
manager miễn phí rồi trả lời quyền sử dụng theo định dạng GUI đang đọc.
Khách không phải nhập key; các `.lic` engine/voice đi kèm vẫn được giữ để
tạo âm thanh. Đây là thay helper trên app review riêng, không sửa bản cài
cá nhân hoặc tự thay toàn bộ luồng auth engine.

Helper chọn `LicenseManager.Current = FreeLicenseManager.Current`, lấy feature
stock và chuyển thành message mà GUI đang đọc từ `ailm.exe validate`. Giữ
codec local stock bằng helper ký tĩnh của framework gốc; không gọi singleton
Pretender hoặc tạo trạng thái kích hoạt/fingerprint. Không đưa key cá nhân
vào source, không sửa engine. Native engine vẫn cần lic runtime đi kèm.

Build: `python3 src/free-client/build.py`, dùng C# compiler có sẵn và reference
assemblies .NET 6 từ MSI, không tải package. Manifest/version/hash ở
`src/free-client/build/manifest.json`. Snapshot UI và manifest nằm ở
`src/free-client/build/app.so` và `app.patch.json`. Chỉ hỗ trợ hash MSI đã kiểm
tra; nếu cập nhật phải kiểm tra lại codec private đang dùng.

## Đối chứng và xác minh

DLL người dùng patch trong shortcut desktop có hash
`83aeee33c39917b94984c3b65abd65d87f09c2e2a2cbc474e955b0504bacfd2e`.
Decompile thấy thay đổi trial 14 ngày → perpetual, không phải chuyển sang
FreeLicenseManager. Thử đúng DLL đó trong prefix sạch vẫn đi qua tạo license
tạm rồi lỗi BrokenWMI/Failed Authentication. Không phủ nhận việc bản đó đang
chạy trên prefix người dùng có trạng thái cũ.

Helper mới + framework stock mở GUI đầy đủ, nạp cả Akane/Aoi/Hime/Mikoto NV
trong namespace offline, prefix mới không có license cá nhân. Xuất WAV qua
GUI được cả bốn giọng. Akane `です。` mặc định 1,290 s; tốc độ 1,50 xuất
1,145 s. Pitch 1,20 đổi PCM; volume 0,50 cho RMS khoảng 0,521 lần mặc định
(engine có xử lý động học, không yêu cầu tỷ lệ biên độ chính xác 0,5).
Aoi block mới 57600 samples, khác Akane 61920 samples. Bản Aoi export đầu
giữ kana block Akane cũ được lưu nhưng không dùng để xác nhận đúng ngữ điệu.

Evidence: [result.json](evidence/free-client/result.json), ảnh/WAV/log dưới
`evidence/free-client/free-helper/` và đối chứng `user-patch/`.
Probe diagnostic `ailm.exe --free-client-info 1` xác nhận manager Free,
IsEnabled/IsAuthenticated=true, IsExpired=false, Product/Perpetual.

Đã kiểm chứng xuất audio; không xác minh nghe qua thiết bị âm thanh thật
trong namespace cô lập, không tuyên bố mọi GUI feature đã qua. Windows VM,
restart/preset persistence và bộ cài tự động vẫn cần kiểm tra tiếp.

## Bản mở cho người dùng test

- Shortcut: `~/.local/share/applications/aivoice2-free-test.desktop`, tên
  **A.I.VOICE2 Free — Test**.
- Launcher: [open-test-gui.sh](../tools/open-test-gui.sh).
- App riêng: `cache/free-client-review/app/`.
- Prefix tự tạo mới: `cache/free-client-review/prefix/`.
- Config chung: `cache/free-client-review/runtime.json`.
- Log launcher mới: `cache/free-client-review/logs/gui.log`; log lịch sử ở
  `cache/free-client-review/gui.log`.

Không đổi shortcut `aivoice2-editor` hoặc app/prefix cá nhân. Đây là bản
review local trước đóng gói, không phải installer phát hành. Muốn quay lại
bản cũ chỉ cần mở shortcut A.I.VOICE2 Editor hiện có.
