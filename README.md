# A.I.VOICE2 + Anki 0.2.0

Kho riêng lưu bộ bàn giao Linux x86-64, trình thiết lập Qt, addon Anki,
runtime đã build và developer-kit cùng tài liệu nghiên cứu.

- Người dùng: bắt đầu tại [START_HERE_VI.md](START_HERE_VI.md), chạy `bash start-setup.sh`.
- Dev hỗ trợ: đọc [chỉ mục bàn giao](developer-kit/docs/DEV_HANDOVER_INDEX_VI.md).
- Source/dev tools: [developer-kit](developer-kit/README.md).
- Kết quả và phạm vi: [release/user-acceptance.json](release/user-acceptance.json).

MSI Editor 2.14.1, Lang và voicebanks được cung cấp riêng, nằm ngoài repo
này. Không đưa activation cá nhân, Wine prefix hoặc bộ cài ứng dụng gốc vào
kho. `build/payload` được theo dõi vì là thành phần runtime của bộ bàn giao.

Đối chiếu file của bản phát hành:

```sh
sha256sum -c SHA256SUMS
```

`SHA256SUMS` và `release-manifest.json` ghi lại bundle 0.2.0 gốc; README,
`.gitignore`, `.gitattributes` quản lý repo được thêm sau, không thuộc danh sách hash gốc.
Các file bundle giữ nguyên để tái hiện bản bàn giao.

Pipeline vntext được phát triển riêng tại
[aquaplatinumberlitz/vntext](https://github.com/aquaplatinumberlitz/vntext).
Bản bundle này không tự nhận các thay đổi streaming/cache mới từ repo đó.
