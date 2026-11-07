# Kiến trúc và source trong repo Anki

Quyết định chung tại [aivoice2api/ARCHITECTURE_VI](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/ARCHITECTURE_VI.md).
Repo này giữ addon và bộ cài/quản lý; backend/API thuộc aivoice2api.
Từ 0.3.0, entry point gốc dùng backend mới; không giữ daemon WAV cũ trên main.

| Đường dẫn | Vai trò |
|---|---|
| `start-setup.sh`, `src/setup/` | Wizard/CLI installer và manager hiện hành |
| `build/payload/runtime/` | Artifact aivoice2api đúng lock, không phải một fork source để sửa tại đây |
| `aivoice2api.lock.json` | Version/commit/checksum artifact được đóng gói |
| `src/anki-addon/` | Source addon hiện hành: dialog, selection/editor, card model |
| `src/free-client/` | Source/tool GUI helper và patch theo baseline |
| `build/payload/gui/`, `build/payload/anki/`, `anki/` | Helper/patch và addon đã đóng gói |
| `tests/` | Test installer, UI, tích hợp, giọng và phiên bản backend |
| `tools/prepare_setup.py` | Đóng gói setup vào output mới từ artifact theo lock |
| `tools/build_release.py` | Kiểm kê/checksum hiện tại, tạo archive bàn giao |
| `archive/docs/`, `archive/notes/`, `archive/tests/` | Hồ sơ RE và tool nghiên cứu theo mốc lịch sử |

Manager đã cài import support từ `<root>/runtime` giống service; checkout
import từ `build/payload/runtime`. Không giữ support/backend riêng dưới
manager/src/daemon hoặc src/daemon. Backend cần sửa thì sửa/test/release
ở aivoice2api, cập nhật lock và toàn bộ runtime artifact cùng manifest.

`src/daemon`, `archive/src/daemon`, bản sao `archive/src/setup`
và tool build backend cũ đã gỡ. Tái hiện 0.2.0 bằng tag v0.2.0 trong checkout
riêng; các finding/evidence giữ lại trên main để dev tra cứu.

Sửa addon chưa tự rebuild artifact; phát hành addon mới cần build .ankiaddon
và cập nhật payload/manifest có chủ đích. Đổi MSI/GUI patch/Lang/Voice baseline
là việc khác với nâng backend. Không nhân bản prefix hay activation cá nhân.
