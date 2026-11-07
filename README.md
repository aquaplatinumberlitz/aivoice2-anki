# aivoice2-anki

Addon Anki và bộ cài/quản lý A.I.VOICE2 trên Linux x86-64. Runtime TTS lấy từ
repo private [aivoice2api](https://github.com/aquaplatinumberlitz/aivoice2api),
được ghim version/commit/checksum bằng `aivoice2api.lock.json`.
[vntext](https://github.com/aquaplatinumberlitz/vntext) là client độc lập dùng
chung backend; không cần mở Anki để phát từ vntext.

- Bắt đầu: [chỉ mục tài liệu](docs/README.md).
- Tạo setup dùng backend chung: [bộ cài](docs/INSTALLER_VI.md).
- Dùng/sửa addon: [ADDON_VI](docs/ADDON_VI.md).
- Source và trách nhiệm: [kiến trúc](docs/ARCHITECTURE_VI.md).
- Hỗ trợ và hồ sơ RE: [runbook hiện hành](docs/SUPPORT_VI.md), [chỉ mục lịch sử](docs/ARCHIVE_INDEX_VI.md).

MSI Editor 2.14.1, Lang và voicebanks cung cấp riêng. Repo không mang
activation cá nhân, Wine prefix hoặc bộ cài ứng dụng gốc.

## Bundle 0.2.0 được giữ để tái hiện

`start-setup.sh` ở gốc chạy bundle WAV lịch sử. `src/daemon`, `build/payload`,
`anki`, `release` và `developer-kit` giữ snapshot gốc; backend mới phát triển
ở aivoice2api. Không sửa chúng để sao chép một fork backend mới vào repo.
Dùng `tools/prepare_setup.py` để compose vào thư mục output riêng theo lock.

```bash
sha256sum -c SHA256SUMS
```

SHA256SUMS/release-manifest.json kiểm các file bundle gốc; README, docs/,
tools/ và metadata quản lý repo được thêm sau. Đọc chỉ mục trước khi dùng
START_HERE hoặc plan cũ: chúng mô tả đúng thời điểm lịch sử, có thể nhắc
workspace đã xóa hoặc giới hạn backend đã được thay thế.
