# Nút Deactivate: lỗi frontend với caption Full version

2026-11-06, helper `1.0.7-free-client.3`, GUI stock 2.14.1.

**Đã sửa và kiểm chứng trên Wine sạch/offline:** UI patch
`2.14.1-free-ui.1` ẩn nút Deactivate cùng lời hướng dẫn và chặn callback cũ.
Bốn thẻ giọng vẫn mang nhãn Full version; xuất WAV qua GUI thành công.
Bản Test được cập nhật riêng, cửa sổ đang mở cần tự khởi động lại.
Đây là kết quả kiểm tra các ca bên dưới, không phải chứng nhận mọi GUI feature.

## Quan sát quyết định

Sau Help → License Authentication → License Confirmation, bấm
`ディアクティベート`, chấp nhận Yes, GUI ghi:

```text
キーの長さが不正です。
Exception: Failed Deactivation...
```

Dòng đầu có nghĩa **độ dài key không hợp lệ**. Trace helper chỉ chứa bốn
lệnh validate khi khởi động, **không có lệnh deactivate**. Do đó lỗi xảy ra
trước khi GUI gọi helper, không phải lỗi trả stdout rỗng từ nhánh deactivate
no-op trong helper và cũng không phải server từ chối license.

## Nguyên nhân

Để phục hồi danh sách voicebank, helper dùng trường `activation_key` làm
caption `Full version`. GUI stock còn dùng cùng trường như activation key
thật khi hủy kích hoạt: kiểm tra độ dài, nhóm các character dùng chung key,
rồi mới gọi quy trình trả license. Caption không có định dạng key nên bước
kiểm tra đầu tiên thất bại.

Thêm caption giải quyết hiển thị nhưng chưa giải quyết chức năng quản lý
activation. Đây là thiếu sót tích hợp của helper mới. Không chứng minh
FreeLicenseManager sai ở tầng cấp quyền, cũng không phải voicebank bị mất.
Không thay/xóa lic hoặc gọi mạng trong lượt test này.

## Bản sửa đã áp dụng

Trong client miễn phí/vĩnh viễn, không có activation cá nhân để thu hồi.
Nên vô hiệu hóa/ẩn nút Deactivate và sửa lời hướng dẫn trang tương ứng,
vẫn giữ danh sách giọng và caption Full version. Source
[gui_patch.py](../src/free-client/gui_patch.py) ghi patch lên bản sao của
snapshot Dart AOT `data/app.so`. Không tạo activation key giả để qua độ
dài; helper `.3` không thay đổi trong lượt sửa này.

Evidence và ảnh: [deactivation](evidence/free-client/deactivation/result.json).
`adapter-calls.jsonl` và `gui.log` cùng thư mục giữ đối chứng.
REA string `Failed Deactivation` ở `0x2d5af0`:
`ev_0eb1112daa0d4db2a4e126891732d3fced3fd8966375883bb5676714084c2ce0`.
Query xrefs string trả rỗng trong provider; không coi là không có caller.
Phân tích một candidate native chưa xác định được callback UI, không dùng
để patch. Debugger chỉ attach bản copy cô lập và đã detach.


## Cơ chế UI để tái sử dụng khi phục dựng

Tên hàm khôi phục từ metadata Dart runtime, offset chỉ áp dụng snapshot
stock 2.14.1 có SHA-256
`1cecf26ccecf3d6e89a6ae7a0962284fbe242cfffe3959f6a9eb052e432d5db6`.
Đây là quan sát bản đã giao và suy luận vai trò từ metadata/assembly,
không phải source Dart gốc.

- `DeactivateLicense.build` bắt đầu `0x9e4d34`. Column chứa bốn child:
  hướng dẫn, khoảng cách, nút, danh sách thẻ. Tại `0x9e515d`, thay đoạn 31
  byte gán ba child đầu bằng const SizedBox có kích thước 0 sẵn trong pool
  (`PP+0x723f`); giữ child thứ tư và biến local chứa mảng.
- `onPressed` closure tại `0x9e52b0`: thay prologue 8 byte bằng
  `mov rax,[r14+0xd0]; ret`, trả Dart null ngay. Không tạo frame, không mở
  xác nhận, không gọi `LicenseManager.deactivate`.
- `LicenseManager.deactivate` tại `0x9e584c`: kiểm tra độ dài key ở
  `0x9e589e` với Smi 46 (23 ký tự), nhánh sai ở `0x9e5b6d`. Không sửa
  manager này vì bản miễn phí không dùng luồng thu hồi activation.

Như người mới có thể hiểu: trang cũ vẫn xây danh sách giọng, nhưng ba món
liên quan đến thu hồi key được thay bằng widget rỗng. Đồng thời hàm mà nút
cũ từng gọi được đổi thành “kết thúc ngay”, để ẩn nút và chặn hành động đều
có hiệu lực. Việc cấp quyền vẫn do helper FreeLicenseManager làm.

Patcher kiểm tra SHA-256 toàn bộ snapshot và từng byte trước khi ghi;
không chấp nhận input đã patch, không ghi đè source. Hai vùng mã dài tổng
39 byte (37 byte thực tế khác giá trị gốc). Output SHA-256:
`99f898840c21ccc20d50d3390ed21e93aafecb99f40456dc9d361784f9ae3e82`.
`build.py` tạo helper, snapshot và cả hai manifest trong một lần build.

## Kiểm chứng hành vi

Hai bản app trong bubblewrap riêng, không mạng, prefix mới, không mount
home/prefix cá nhân. Dùng helper `.3` và bốn NV công ty cấp:

1. **Patch đầy đủ:** License Confirmation không còn nút/lời hướng dẫn;
   Akane/Aoi/Hime/Mikoto đều hiện Full version. Quay lại Editor và trở lại
   trang license vẫn đúng bố cục ở kích thước cửa sổ khác.
2. **Chỉ patch callback:** giữ nguyên UI stock để bấm được nút cũ. Bấm ba
   lần liên tiếp, bấm thêm một lần và phím Space không mở xác nhận/lỗi.
   Trace helper chỉ có bốn validate khởi động, không có deactivate.
3. **Xuất âm thanh:** từ GUI patch đầy đủ, Akane NV mặc định với `です。`
   xuất WAV mono, PCM 16-bit 48 kHz, 61.920 samples, 1,29 giây, peak 9448.
   Log không chứa Failed Deactivation, invalid-key-length hoặc lỗi widget.
4. **Khởi động lại:** mở lại GUI trong cùng prefix cô lập, cả bốn giọng
   vẫn nạp, trang license tiếp tục ẩn nút/lời hướng dẫn.
5. **Build:** tái tạo đúng hash; từ chối snapshot không hỗ trợ/đã patch;
   từ chối output trùng source; diff chỉ nằm trong hai vùng đã khai báo.

Ảnh, trace, WAV, manifest và thông tin phép thử:
[deactivation-ui/result.json](evidence/free-client/deactivation-ui/result.json).
Không xác nhận nghe qua loa vật lý trong Xvfb; chưa thử patch này trên Windows VM.

## Triển khai và quay lại

Chỉ cập nhật `cache/free-client-review/app/data/app.so` bằng thay file nguyên tử.
Backup stock ở `cache/free-client-review/gui-backups/app.stock-2.14.1.so`,
manifest triển khai ở `cache/free-client-review/gui-patch-manifest.json`.
Không tắt cửa sổ GUI review người dùng đang làm việc; mở lại shortcut
**A.I.VOICE2 Free — Test** để nạp snapshot mới. Bản Editor cá nhân và MSI
không bị sửa. Khôi phục backup khi bản Test đã đóng để lùi patch UI.
