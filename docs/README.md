# Tài liệu aivoice2-anki

Bản hiện hành **0.3.0**: repo sở hữu addon và bộ cài/quản lý, đóng gói runtime
mới từ aivoice2api. `bash start-setup.sh` dùng backend đó ngay; không cần compose.

| Công việc | Tài liệu |
|---|---|
| Cài và dùng nhanh | [START_HERE_VI](../START_HERE_VI.md) |
| Ranh giới source | [Kiến trúc Anki](ARCHITECTURE_VI.md) |
| Bộ cài/checksum/release/dependency | [INSTALLER_VI](INSTALLER_VI.md) |
| Editor/addon và chèn media | [ADDON_VI](ADDON_VI.md) |
| Chẩn đoán, quản lý giọng và rollback | [SUPPORT_VI](SUPPORT_VI.md) |
| Finding/evidence/plan lịch sử | [ARCHIVE_INDEX_VI](ARCHIVE_INDEX_VI.md) |

Tài liệu chung chỉ duy trì ở aivoice2api:
[kiến trúc](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/ARCHITECTURE_VI.md),
[kết nối](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/CONNECT_VI.md),
[API](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/API_VI.md),
[build backend](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/RELEASE_VI.md).

`developer-kit/docs` và notes chứa lịch sử RE theo binary/commit, có thể
nhắc đường dẫn cũ đã gỡ. Test/setup hiện hành ở tests/src/setup; backend
hiện hành trong artifact theo lock. Bản 0.2.0 tái hiện bằng tag v0.2.0.
