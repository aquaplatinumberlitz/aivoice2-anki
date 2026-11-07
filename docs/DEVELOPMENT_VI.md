# Dev mới: sửa đúng phần, kiểm đúng artifact

Cài và nghe câu mẫu trước theo [Quickstart](QUICKSTART_VI.md). Đây là hướng
dẫn sửa/build; khách chỉ cài phần mềm không cần các bước dưới.

## Chọn repo và source

| Thay đổi | Nơi sửa |
|---|---|
| Mic/dialog/selection, field/media/card | `src/anki-addon/` trong repo này |
| Wizard, cài app, quản lý giọng và tích hợp desktop | `src/setup/` trong repo này |
| Helper/patch GUI theo binary baseline | `src/free-client/` trong repo này |
| HTTP, scheduler, WAV quota, worker Wine/ABI | [aivoice2api/runtime](https://github.com/aquaplatinumberlitz/aivoice2api/tree/main/runtime) |
| Overlay, extraction, prepare/lookahead/player | [vntext/src](https://github.com/aquaplatinumberlitz/vntext/tree/main/src) |

`build/payload/runtime` là bản phân phối theo lock, không sửa ở đây để tạo
fork backend. `archive/` giữ finding/tool cũ, không phải điểm bắt đầu sửa.
Xem [kiến trúc](ARCHITECTURE_VI.md) để hiểu source khác runtime đã cài.

## Test installer và addon

Tại gốc repo:

```bash
python3 -m unittest discover -s tests -v
python3 src/anki-addon/install.py --package-only --output ./build/aivoice2-local.ankiaddon
```

Lệnh addon chỉ build archive, không cài vào profile thật. So artifact mới
với artifact trước khi triển khai; sửa source chưa tự cập nhật addon đã
cài hoặc hai file package trong anki/ và build/payload/anki/.

Thay addon cần test profile thử: editor được hỗ trợ, chọn câu Nhật, thay
nội dung/giọng trong lúc chờ, preview không chèn và đồng ý chèn đúng field.
Không mở collection khách để test hoặc tự gửi thoại/media vào log.

## Đóng gói sau thay đổi

Bump VERSION của bộ cài nếu thay file phát hành. Backend có version riêng;
chỉ đổi lock khi thay runtime artifact được kiểm chứng. Theo
[INSTALLER_VI](INSTALLER_VI.md) để cập nhật manifest/checksum, kiểm gói giải
nén và tạo release mới. Không upload nội dung khác vào asset/tag cũ.

Helper GUI build theo [src/free-client/README](../src/free-client/README.md).
Giữ nguyên bản stock để rollback và kiểm đúng baseline; việc sửa UI không
phải cách chữa lỗi backend/client. Không tự chạy probe RE lên prefix khách.
