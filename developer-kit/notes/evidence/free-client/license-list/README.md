# License Confirmation trống: tương thích metadata GUI

**Cập nhật helper .3:** người dùng yêu cầu đổi caption từ `Free client` thành
`Full version`. Evidence trước/sau của .2 bên dưới giữ nguyên để bảo toàn
đối chứng lỗi danh sách; manifest và kết quả kiểm tra caption .3 lưu riêng
trong `full-version-caption.json`.

Ngày 2026-11-06. Người dùng báo voicebank có thể dùng nhưng không xuất hiện
ở Help → License Authentication → ライセンス確認 (License Confirmation).

## Nguyên nhân và đối chứng

Helper .1 gửi `activation_key: ""` trong claim validate, mục đích không
đưa key cá nhân vào client Free. Màn hình License Confirmation của GUI
stock dùng trường này để lọc/hiển thị các mục: rỗng thì danh sách trống.

Thử .1 trên prefix sạch/offline tái hiện danh sách trống, dù nạp được cả bốn
NV. Giữ nguyên app/framework/engine, chỉ đổi giá trị activation_key thành
nhãn `Free client` thì GUI hiện lại đủ Akane/Aoi/Hime/Mikoto NV, mỗi thẻ
hiển thị nhãn đó. Đây là bằng chứng runtime của điều kiện hiển thị, không
phải khẳng định đã khôi phục toàn bộ source code bộ lọc UI.

Nhãn là trạng thái client miễn phí, không phải license cá nhân. Native auth
engine/voicebank và quyền Product/Perpetual từ FreeLicenseManager giữ nguyên.

## Trace đã thu

GUI khởi động gọi helper một lần cho mỗi feature, không gọi lại validate
khi chỉ mở màn hình License Confirmation:

```text
validate 2319 --product "A.I.VOICE2 Editor"
validate 2320 --product "A.I.VOICE2 Editor"
validate 2514 --product "A.I.VOICE2 Editor"
validate 2515 --product "A.I.VOICE2 Editor"
```

GUI dùng metadata giọng đã nạp để vẽ tên/ảnh; không cần thay product claim
thành tên voicebank. Việc đổi product là không cần thiết cho lỗi này.

Kiểm tra helper final .2: bốn feature trên trả claim nontrial/perpetual,
caption `Free client`, product `A.I.VOICE2 Editor`. Restart GUI trong prefix
test, trace chỉ có validate và vẫn nạp đủ bốn giọng. Cần khởi động lại bản
review để GUI đọc lại claim mới vì danh sách dùng dữ liệu giữ trong bộ nhớ.

## File bằng chứng

- `before/`: manifest/ảnh và trace helper để caption rỗng.
- `after/`: ảnh danh sách có caption, claim đã decode, trace và log restart.
- `ailm-label-trial.dll`: candidate đổi riêng caption để đối chứng.
- `final-adapter-manifest.json`: helper .2 đã kiểm tra và đưa vào review.
- `rea-gui-activation-field.json`: retained REA bundle. Query string
  `activation_key` trong app.so:
  `ev_446704774e1ab0ea0b1d32417ba73b59539d731e16f7d12750371b8ea6a5724d`,
  địa chỉ provider `0x361370`; string một mình không chứng minh điều kiện lọc.

Runner có thể tái lập qua `tests/gui_license_probe.py --gui-only
--license-adapter ... --trace-adapter` trong PTY. Trace opt-in chỉ giữ ID và
product của validate, các tham số quản lý kích hoạt được lược bỏ để tránh
ghi key nhập vào. Log test chỉ dùng các file công ty cấp, không gọi mạng.
