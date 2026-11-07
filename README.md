# aivoice2-anki 0.3.0

Addon Anki và bộ cài/quản lý A.I.VOICE2 trên Linux x86-64. Bộ cài mặc định
đã dùng runtime [aivoice2api 0.1.0](https://github.com/aquaplatinumberlitz/aivoice2api/releases/tag/v0.1.0),
có WAV, PCM streaming, warm/prepare/cancel và quota cache. Version, commit
và checksum backend được ghim trong `aivoice2api.lock.json`.

```bash
bash start-setup.sh
```

Không cần tải hoặc compose backend trước khi dùng. `build/payload/runtime`
là artifact backend mới đã đóng gói; source chính chỉ ở repo aivoice2api.
Anki dùng API WAV; vntext dùng cùng service và thương lượng PCM streaming.

- Bắt đầu: [START_HERE_VI](START_HERE_VI.md), [chỉ mục tài liệu](docs/README.md).
- Bộ cài/build/checksum: [INSTALLER_VI](docs/INSTALLER_VI.md).
- Dùng/sửa addon: [ADDON_VI](docs/ADDON_VI.md).
- Source và trách nhiệm: [kiến trúc](docs/ARCHITECTURE_VI.md).
- Hỗ trợ/RE: [runbook](docs/SUPPORT_VI.md), [chỉ mục lịch sử](docs/ARCHIVE_INDEX_VI.md).

MSI Editor 2.14.1, Lang và voicebanks cung cấp riêng. Repo không mang
activation cá nhân, Wine prefix hoặc bộ cài ứng dụng gốc.

Các bản fork backend WAV cũ đã gỡ khỏi main; bản 0.2.0 còn trong lịch sử
Git/tag `v0.2.0`. Checksum hiện tại áp dụng cho 0.3.0:

```bash
python3 tools/build_release.py
sha256sum -c SHA256SUMS
```

Cài mới dùng root mới; chạy setup không tự nâng cấp root đang tồn tại.
Runtime đã cài được nâng có backup/receipt theo hướng dẫn backend chung.
