# Source helper và patch GUI hiện hành

Thư mục này thuộc source bộ cài, không là backend aivoice2api. Người cài
bình thường dùng [Quickstart](../../docs/QUICKSTART_VI.md); helper/UI đã có
sẵn trong payload và setup sẽ áp dụng đúng baseline.

| File | Vai trò |
|---|---|
| LicenseAdapter.cs | Helper ailm.dll dùng FreeLicenseManager cho GUI |
| gui_patch.py | Patch UI app.so đúng hash: danh sách Full version, UX Deactivate |
| build.py | Build helper/patch từ bản stock 2.14.1 vào thư mục output riêng |

Dev build cần .NET 8 SDK và bản app **stock trích từ MSI**. Từ gốc repo:

```bash
python3 src/free-client/build.py --msi-app '/duong/dan/app-stock' --output-dir ./src/free-client/build
```

Đổi `/duong/dan/app-stock` thành đường dẫn thật trước khi chạy. Tool kiểm
framework stock; không dùng app đã patch làm input. Output là ailm.dll,
app.so và manifest/patch report; lệnh không triển khai vào bản đang dùng.
Sau review cần cập nhật payload/phát hành có chủ đích, giữ file stock và
backup. Không suy rộng patch 2.14.1 sang binary khác.

Cơ chế và bằng chứng RE theo mốc lịch sử:
[FREE_CLIENT_GUIDE](../../archive/notes/FREE_CLIENT_GUIDE_VI.md),
[review](../../archive/notes/FREE_CLIENT_REVIEW.md),
[Deactivate](../../archive/notes/FREE_CLIENT_DEACTIVATION.md).
Launcher/probe workspace cũ được giữ trong archive, không là công cụ mở
GUI cho khách; dùng nút Mở A.I.VOICE2 hoặc shortcut manager đã cài.
