# Kiến trúc và source trong repo Anki

Quyết định chung tại [aivoice2api/ARCHITECTURE_VI](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/ARCHITECTURE_VI.md).
Repo này tiếp tục giữ cả addon và bộ cài/quản lý; backend/API thuộc aivoice2api.

| Đường dẫn | Vai trò và trạng thái |
|---|---|
| `tools/prepare_setup.py` | Compose setup dùng artifact backend theo lock; entry point build hiện hành |
| `aivoice2api.lock.json` | Version/commit/checksum backend đã chọn để đóng gói và QA |
| `developer-kit/src/anki-addon/` | Source addon hiện có: dialog, selection/editor compatibility, card model; sửa addon tại đây và build lại artifact khi phát hành |
| `src/setup/` | Template manager Qt/installer từ bundle 0.2.0; compose có adapter cho kết quả Engine.speak mới |
| `developer-kit/src/free-client/` | Source/tool helper và GUI patch gắn đúng baseline; không chuyển vào backend |
| `build/payload/`, `anki/` | Artifact 0.2.0 gốc; không sửa để nâng backend |
| `src/daemon/`, `developer-kit/src/daemon/` | Snapshot backend lịch sử; không phát triển backend ở đây |
| `release/`, SHA256SUMS, release-manifest.json | Baseline/phạm vi/hash bundle gốc |
| `developer-kit/docs/`, `notes/`, `tests/` | Hồ sơ kỹ thuật, RE, evidence và tool theo thời điểm bàn giao; xem ARCHIVE_INDEX |
| `build/setup-aivoice2api-*/` | Output compose bị gitignore; chứa template đã thích nghi và runtime chính từ artifact |

Compose không download ngầm hoặc dùng backend trên máy dev. Nó kiểm archive
với lock, kiểm manifest từng file, ghép runtime vào payload mới và tạo lại
payload manifest. Các file trong bundle gốc vẫn còn kiểm checksum được.

Thay backend: sửa/test/release trong aivoice2api rồi cập nhật lock và compose.
Thay addon: sửa source addon, build .ankiaddon bằng tool đã ghi trong dev-kit,
kiểm preview/chèn media/editor và tạo bản phát hành Anki mới. Không coi việc
sửa source là addon trong payload hoặc máy khách đã được thay tự động.

Đổi MSI, GUI patch hoặc Lang/voicebank baseline là công việc khác với nâng
backend. Giữ dữ liệu khách, backup và bằng chứng đúng version khi xử lý.
