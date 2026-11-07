# aivoice2-anki

Bộ cài A.I.VOICE2 trên Linux và addon phát tiếng Nhật trong Anki.
Đã kèm **backend mới aivoice2api 0.1.0**, dùng chung được với vntext.

**[Bắt đầu A–Z: cài backend → Anki → vntext](docs/QUICKSTART_VI.md)**

**[Tải bộ cài 0.3.1](https://github.com/aquaplatinumberlitz/aivoice2-anki/releases/tag/v0.3.1)**
→ Assets → `aivoice2-anki-0.3.1.tar.gz` → giải nén → mở thư mục → chạy:

```bash
bash start-setup.sh
```

Nhận riêng MSI Editor 2.14.1, Lang và voicebanks từ bên bàn giao; chúng
không nằm trong repo. [Chuẩn bị môi trường](docs/ENVIRONMENT_VI.md) nếu máy
chưa có Wine/Qt/msitools. Anki native cần cài và mở ít nhất một lần.
Repo/Release là private: nếu 404, cần quyền đọc hoặc nhận gói trực tiếp.

## Chọn đúng tài liệu

| Bạn cần | Đọc |
|---|---|
| Cài và nối hai app từ đầu | [Quickstart chung](docs/QUICKSTART_VI.md) |
| Dùng mic, chọn field và chèn media | [Addon](docs/ADDON_VI.md) |
| Thêm/gỡ/khôi phục giọng | [Quản lý giọng](docs/VOICES_VI.md) |
| Xử lý lỗi sau cài | [Hỗ trợ](docs/SUPPORT_VI.md) |
| Dev sửa/build/đóng gói | [Hướng dẫn dev](docs/DEVELOPMENT_VI.md), [bộ cài](docs/INSTALLER_VI.md) |
| Tìm toàn bộ docs hoặc nghiên cứu cũ | [Chỉ mục](docs/README.md) |

## Bố trí repo

```text
src/anki-addon/     source addon đang dùng
src/setup/          wizard và quản lý bản cài
src/free-client/    source helper và patch GUI theo baseline
build/payload/      runtime aivoice2api + GUI/addon đã đóng gói
anki/               addon .ankiaddon để cài thủ công
docs/               hướng dẫn hiện hành
archive/            finding RE, evidence và kế hoạch lịch sử
tests/, tools/      kiểm tra, đóng gói và manifest
```

Source backend chính ở [aivoice2api](https://github.com/aquaplatinumberlitz/aivoice2api).
Người cài thường không cần clone repo đó; dev cập nhật runtime theo
`aivoice2api.lock.json`. [vntext](https://github.com/aquaplatinumberlitz/vntext)
là client riêng; không cần mở Anki/Editor để vntext đọc tiếng Nhật.

Cài mới vào root mới; setup không cài đè bản đang có. Các bản cũ giữ trong
tag Git, hồ sơ RE ở archive không phải hướng dẫn cài hiện hành.
