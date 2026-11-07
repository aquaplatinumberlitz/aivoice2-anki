# Helper cho A.I.VOICE2 Free client

Hướng dẫn tiếng Việt cho người mới, gồm cơ chế, sơ đồ, build, cập nhật và
quay lại bản cũ: [FREE_CLIENT_GUIDE_VI.md](../../notes/FREE_CLIENT_GUIDE_VI.md).

- [LicenseAdapter.cs](LicenseAdapter.cs): logic helper thay `ailm.dll`.
- [build.py](build.py): build riêng, kiểm tra framework stock 2.14.1.
- [gui_patch.py](gui_patch.py): patch UI đúng hash stock 2.14.1; ẩn nút và
  lời hướng dẫn Deactivate, chặn callback, giữ danh sách Full version.
- [open-test-gui.sh](open-test-gui.sh): mở app/prefix review trên máy hiện tại.
- [FREE_CLIENT_REVIEW.md](../../notes/FREE_CLIENT_REVIEW.md): kết quả và giới hạn test.

Khách dùng GUI không cần build hoặc chạy lệnh diagnostic.

`python3 src/free-client/build.py` tạo `build/ailm.dll`, `build/manifest.json`,
`build/app.so` và `build/app.patch.json`. Chỉ ghi vào thư mục build, không
triển khai vào app đang chạy. App review cần cả helper và UI patch; framework,
engine, dữ liệu và file runtime vẫn dùng bản stock/công ty cấp.

Kiểm tra cô lập trên prefix mới, không mạng, không trạng thái cá nhân:

```sh
python3 tests/gui_license_probe.py --gui-only \
  --license-adapter /home/admin/aivoice2-re/src/free-client/build/ailm.dll \
  --gui-snapshot /home/admin/aivoice2-re/src/free-client/build/app.so \
  --trace-adapter
```

Chạy probe với PTY; gửi từng dòng JSON argv để thao tác bên trong namespace,
gửi `quit` để dừng các process thuộc phép thử. Kết quả:
[FREE_CLIENT_DEACTIVATION.md](../../notes/FREE_CLIENT_DEACTIVATION.md).
