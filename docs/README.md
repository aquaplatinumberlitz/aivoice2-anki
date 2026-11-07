# Tài liệu aivoice2-anki

Kiến trúc hiện hành ngày 2026-11-07: repo này sở hữu **addon và bộ cài/quản
lý**, lấy runtime từ `aivoice2api`; vntext là client độc lập.

| Người đọc/công việc | Tài liệu hiện hành |
|---|---|
| Hiểu repo và source nào được sửa | [Kiến trúc Anki](ARCHITECTURE_VI.md) |
| Build setup dùng backend được ghim, cài mới | [Bộ cài](INSTALLER_VI.md) |
| Phát thử, chèn media, chỉnh editor/addon | [Addon](ADDON_VI.md) |
| Chẩn đoán backend, addon, voicebank và rollback | [Hỗ trợ](SUPPORT_VI.md) |
| Đọc RE, evidence, plan và bundle cũ | [Chỉ mục lịch sử](ARCHIVE_INDEX_VI.md) |

Tài liệu chung chỉ duy trì tại aivoice2api:
[kiến trúc ba repo](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/ARCHITECTURE_VI.md),
[kết nối hai client](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/CONNECT_VI.md),
[API](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/API_VI.md),
[build/release](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/RELEASE_VI.md).

`START_HERE_VI.md`, `CHANGELOG.md`, `release/`, `src/daemon`, `build/payload`
và `developer-kit/` vẫn mô tả bundle 0.2.0 hoặc các mốc nghiên cứu trước đó.
Chúng giữ nguyên byte để checksum/evidence còn có giá trị. Trong câu hỏi
về kiến trúc hiện tại, ưu tiên docs/ này và source backend được ghim;
không làm theo hướng dẫn workspace cũ như thể nó là bản cài hiện hành.
