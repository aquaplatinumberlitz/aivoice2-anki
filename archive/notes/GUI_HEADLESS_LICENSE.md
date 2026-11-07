# GUI và headless: hai lớp license — thử ngày 2026-11-06

## Kết luận trong phạm vi đã thử

- **Headless không yêu cầu kích hoạt cá nhân:** engine nguyên bản tổng hợp
  offline với `aitalk.lic` từ MSI và `voice.lic` công ty cấp, không registry
  kích hoạt, không GUI hoặc license manager. Lượt sạch trước xác nhận cả bốn
  NV, xem [CLEAN_RUNTIME.md](CLEAN_RUNTIME.md).
- **Không đồng nghĩa bỏ mọi file `.lic`:** các ca mới bỏ auth, truyền NULL,
  chuỗi rỗng hoặc đường dẫn không tồn tại đều thất bại trên API đã thử.
  Chưa tìm thấy nhánh headless bỏ license file trong các entry point này;
  không tuyên bố mọi API/bản build khác đều không có chế độ đó.
- **GUI stock có kiểm tra license sản phẩm riêng:** dù đủ file runtime,
  nó tìm thông tin license cục bộ rồi thử tạo license tạm. Trong Wine sạch,
  bước này lỗi `BrokenWMI` và GUI hiện `Failed Authentication`.
- Bỏ toàn bộ `.lic` khỏi app thử khiến GUI lỗi sớm hơn:
  `License not authenticated` khi tạo Talker, còn ở màn hình loading.

Do lỗi WMI, **chưa chứng minh GUI trên Windows luôn cần key trả phí**, hoặc
GUI có license tạm/trial hợp lệ có chạy được không. Quan sát xác nhận GUI có
luồng license bổ sung mà worker headless không thực thi. Đây không phải ca
GUI có license cá nhân thành công đối chứng; không suy rộng lỗi Wine thành
chính sách cấp phép của mọi nền tảng.

## Headless: ma trận runtime

Mỗi ca chạy process engine mới, không sửa DLL. Aoi NV, câu `です。`, UTF-8 0:

| Ca | Auth/talker/voice | Kết quả |
| --- | --- | --- |
| Không gọi authenticate | initialize=0, talker=NULL | exit 5 |
| Authenticate với path NULL | auth=-3, talker=NULL | exit 5 |
| Engine license không tồn tại | auth=-7, talker=NULL | exit 5 |
| Đủ engine lic, voice lic NULL | auth=0, loadVoiceDic=-3 | exit 6 |
| Đủ engine lic, voice lic rỗng | auth=0, loadVoiceDic=-3 | exit 6 |
| Đủ engine lic, voice lic không tồn tại | auth=0, loadVoiceDic=-7 | exit 6 |
| Đủ file nguyên bản | auth=0, loadVoiceDic=0, talk=0 | exit 0, PCM 115200 bytes |

Lượt GUI bỏ `.lic` có thêm ca headless trong cùng cây app **không còn bất kỳ
file `.lic` nào**: initialize=0, bỏ auth → talker=NULL, exit 5. Không có fallback
tự tìm license khi khởi tạo theo cách này.

Nguồn probe: [tests/headless_license_probe.c](../tests/headless_license_probe.c),
chỉ gọi export stock, không patch flag xác thực, không thay file license.
Không đưa thay đổi vào worker/addon production.

## GUI: nguồn và cô lập

App copy đầy đủ từ MSI gốc, gồm **AI.Framework.License.dll nguyên bản MSI**
SHA-256 `10d3493f360ca6a8a8fc6138081b3e79469485197689614c2b2581f772602797`.
Không dùng hai DLL đứng cạnh MSI, cũng không dùng license manager trong bản
đã cài (hash khác). Lang và bốn NV lấy từ công ty cấp. Copy engine cùng hash
ra app root để nằm cạnh dependency native như layout installation đã quan sát.

Mỗi lượt GUI có prefix mới, hostname và machine-id thử riêng, không mạng,
không home/registry/prefix cá nhân. Runtime và app read only, chỉ `/work`
writable. Xvfb chạy bên trong namespace, không dùng display người dùng.
`LIBGL_ALWAYS_SOFTWARE=1` và Mesa EGL tránh crash NVIDIA EGL khi không có GPU
trong namespace. Không sửa giấy phép hoặc giả lập trạng thái kích hoạt.

Nguồn runner: [tests/gui_license_probe.py](../tests/gui_license_probe.py).
Chạy với PTY để gửi command chẩn đoán qua stdin, ví dụ:

```sh
python3 tests/gui_license_probe.py
python3 tests/gui_license_probe.py --gui-only
python3 tests/gui_license_probe.py --gui-only --omit-licenses
```

Stdin nhận JSON argv, ví dụ `["import","-window","root","/work/gui-start.png"]`;
`quit` dừng Wine/Xvfb của riêng lượt thử. Runner cần thư mục MSI đã extract
và assets công ty đúng đường dẫn ở CLEAN_RUNTIME.md.

GUI đầy đủ file ghi các dòng:

```
ライセンス情報の取得に失敗、もしくはライセンス情報がローカルに存在しません。
暫定ライセンスを作成します。
暫定ライセンスの作成に失敗しました。
    message: BrokenWMI
Exception: Failed Authentication...
```

Dịch: không lấy được/không có thông tin license cục bộ → tạo license tạm →
không tạo được, lỗi BrokenWMI → xác thực thất bại. `wmic` trong container
trả UUID `deaddead-dead-dead-dead-deaddeaddead` và BIOS serial chung của Wine;
đây là quan sát môi trường, chưa xác định đầy đủ thuật toán fingerprint.

## RE có thể tái sử dụng

- `ai_Talker_newEx` tại `0x1800C4600` cũng kiểm tra byte authenticated
  `byte_1803A62DD`; nhánh chưa auth ghi lỗi `Unauthenticated` và trả NULL.
  Evidence `ev_3350c24d8ef8fa721354a4e7c90ceca3321982f01ec4507fd34e98d5bde3df3c`.
  Hàm nhận con trỏ obj, không có bằng chứng đây là cờ headless bỏ auth.
- Assembly license manager có `FreeLicenseFeature`, `FreeLicenseManager`,
  `PretenderLicenseManager`. `.cctor` của `LicenseManager` gọi getter
  FreeLicenseManager và gán current. **Có class Free không chứng minh GUI
  cuối cùng dùng class đó:** runtime GUI vẫn ghi luồng license tạm kể trên.
  Metadata/CIL giữ nguyên token build-local, không tải hoặc thực thi assembly
  khi phân tích tĩnh. User-string metadata có cảnh báo partial; không dùng
  kết quả search thiếu để tuyên bố không có API khác.
- Managed artifact evidence:
  `ev_1ef63f3a7e19c88b5498aa52abe4632a890fcc31a2a175b2862c4613d15a6102`;
  chọn Free/LicenseManager:
  `ev_81680b5597b51c711083af0e61e8ae5195f76fe8a0bf8c93cb48528c05ad4202`.

## Evidence giữ lại

- [summary.json](evidence/clean-runtime/gui-headless/summary.json): kết quả
  ma trận, hai GUI và giới hạn.
- [Headless matrix](evidence/clean-runtime/gui-headless/headless-matrix/headless-matrix.json):
  stdout và exit từng process; log đầy đủ cùng thư mục.
- [GUI đủ runtime lic](ARCHIVE_COVERAGE.md):
  hộp thoại Failed Authentication; `gui.log` giữ lỗi BrokenWMI.
- [GUI không có lic](ARCHIVE_COVERAGE.md):
  loading; `gui.log` giữ lỗi Talker và `no-files-headless.json` giữ đối chứng.
- Manifest và isolation-command của từng lượt nằm cùng thư mục tương ứng.
- [REA bundle](evidence/clean-runtime/gui-headless-rea.json): 5 records.

Artifacts local: `cache/gui-license-xg1wk_w2` (matrix),
`cache/gui-license-vwczv_vf` (GUI đủ file), `cache/gui-license-yomwtj7c` (GUI
bỏ file lic). Hai lượt đầu Xvfb/PTY lỗi cũng được giữ trong cache nhưng không
dùng để kết luận GUI; lượt sau đã chạy và chụp được cửa sổ thật.

## Hệ quả cho Anki

Client Anki có thể giữ engine + file runtime được công ty cấp, tự auth nội
bộ, khách không nhập key/kích hoạt sản phẩm GUI. Không cần chạy Editor.
Không xóa file `.lic` khỏi bundle dựa trên cách gọi “headless không cần lic”;
nếu công ty muốn nói tới một API/cờ cụ thể khác, cần tên entry point/cấu hình
hoặc bản build tương ứng để kiểm tra tiếp.
