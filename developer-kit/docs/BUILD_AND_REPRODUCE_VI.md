# Build và tái tạo cho dev

Runtime khách không cần compiler. Dev build dùng Linux x86-64, Python 3,
MinGW x86_64, .NET 8 SDK và msitools. Phiên bản đã quan sát ghi trong
`release/toolchain-observed.json`; distro/Wine khác cần chạy lại QA.
GUI 0.2.0 cần PySide6 hoặc PyQt6; nghe thử dùng Qt Multimedia/mpv.

## Build từ source và input riêng

Chạy từ thư mục source có `src/`, `tools/`, `release/`. MSI và dữ liệu công
ty cấp đặt ngoài source. Thay các đường dẫn mẫu bằng vị trí của bạn:

```sh
msiextract -C ./stock-extract /path/to/AIVoice2Editor.msi
python3 tools/build_payload.py \
  --msi-app ./stock-extract/ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor \
  --output ./build/payload-new
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 src/setup/manager.py --payload ./build/payload-new
```

Payload builder gọi worker/helper/addon build, không mở/cài Anki hoặc sửa
app cá nhân. Phải chọn thư mục output mới. Worker production không tự biên
dịch. Compiler helper tự tìm .NET 8 SDK, có CLI riêng để chọn `csc.dll`.

Hash helper đã kiểm chứng:
`f2476c10be34b815d34cd111c07a82f996adb8a114c3ff60971e0029b8b612b3`.
Hash snapshot UI sau patch:
`99f898840c21ccc20d50d3390ed21e93aafecb99f40456dc9d361784f9ae3e82`.
Đổi compiler có thể đổi byte output; kiểm manifest và QA, không tự thay
hash baseline chỉ để bỏ lỗi. Source/ABI native phải giữ đúng bản đã xác minh.

## Tái lập input baseline

```sh
python3 tools/release_baseline.py --msi /path/to/AIVoice2Editor.msi \
  --msi-app ./stock-extract/ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor \
  --assets-dir /path/to/company-assets --output ./release-inputs-rechecked.json
```

Tool chỉ đọc input, inventory hash và đối chiếu evidence clean-run. Bốn NV
công ty cấp là baseline dữ liệu tham chiếu. Từ 0.1.1, installer còn import
voicebank do khách chọn ngoài baseline, tự lưu hash và cấu hình dialect;
không nhúng các bank đó vào bộ tích hợp. Không thay `.lic` bằng file rỗng/NULL.

## Kiểm thử sâu

```sh
python3 tests/setup_clean_probe.py --payload ./build/payload-new \
  --msi /path/to/AIVoice2Editor.msi --assets-dir /path/to/company-assets
```

Probe cần bubblewrap, Xvfb, ImageMagick/xdotool và Anki dev dependencies.
Nó dựng prefix mới/offline, cài riêng Aoi, thêm Akane/Kansai, gỡ default,
khôi phục, kiểm chặn thay giọng khi engine đang chạy và chạy pipeline addon
trên editor mới/cũ. `passed: true` chỉ xác nhận các ca được ghi, không xác
nhận đã nghe loa thật hoặc systemd user activation trong namespace không có bus.

Các probe nghiên cứu cũ có thể cần layout `cache/`/input cụ thể. Đọc mô tả
script trước; không chạy `poc.c` cũ làm mẫu ABI hoặc chạy proxy trên app khách.

## Đóng gói

`tools/build_handover.py` lấy payload đã build và allowlist source/docs/tool.
Output là candidate local, không tự upload/phát hành. Bộ runtime dùng được
ngay với input riêng; developer-kit kèm source và bản evidence đã biên tập.
Kiểm `SHA256SUMS`, release manifest và QA từ chính bundle trước bàn giao.
