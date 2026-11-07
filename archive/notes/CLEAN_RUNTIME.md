# Thử runtime trên môi trường sạch — 2026-11-06

Phân biệt thêm file license runtime với kích hoạt GUI, cùng ma trận bỏ
auth/NULL/missing lic và ảnh GUI nguyên bản:
[GUI_HEADLESS_LICENSE.md](GUI_HEADLESS_LICENSE.md).

## Kết quả

**Cập nhật sau khi công ty cấp Lang/voicebanks:** lượt thử thứ hai dùng toàn
bộ engine/DLL/aitalk.lic trích từ MSI gốc và lang/voicebanks công ty cấp tại
`[AUTHOR_HOME]/Downloads/A.I.VOICE2 2.14.1/`. Không dùng asset từ bản đã cài.
Cả **Akane NV, Aoi NV, Meika Hime NV, Meika Mikoto NV** đều qua: tám WAV,
hai câu mỗi giọng, trong prefix mới khác và offline. Các negative control
thiếu engine/voice license vẫn thất bại đúng như lượt đầu.

`voice.lic` Akane NV và Aoi NV công ty cấp khớp từng byte bản đã cài. Nguồn
hai file đó đã được đối chiếu trực tiếp; không còn chỉ dựa vào license trên
máy cá nhân. Hime/Mikoto dùng đúng file công ty mới cấp. Với bộ bốn giọng này,
đã đủ thành phần để làm runtime client không yêu cầu khách nhập key cá nhân,
giữ cơ chế auth nội bộ với các file đi kèm, chưa cần sửa binary.

Bằng chứng lượt công ty cấp:
[result.json](evidence/clean-runtime/company-assets/result.json),
[manifest.json](evidence/clean-runtime/company-assets/manifest.json),
[audit.json](evidence/clean-runtime/company-assets/audit.json),
[company-asset-comparison.json](evidence/clean-runtime/company-asset-comparison.json).
Đây là xác minh kỹ thuật bộ file công ty cung cấp, không suy rộng sang mọi
bản sản phẩm hoặc mọi voicebank chưa được công ty cấp.

Các mục bên dưới giữ chi tiết **lượt đầu** dùng chín voicebank đã cài để
phân biệt hai nguồn. Phần còn thiếu nguồn bộ cài ở lượt đầu đã được giải
quyết cho Akane/Aoi NV ở lượt thứ hai; bảy voice legacy/galaco chưa có trong
bộ công ty mới cấp. Không tự đưa hai Meika mới vào addon production trong
lượt kiểm tra riêng này.

**Đã qua:** engine nguyên bản trích từ MSI xác thực, tạo talker và tổng hợp
18 WAV (hai câu × chín voicebank) trong Wine prefix hoàn toàn mới, offline.
Không sao chép Wine prefix, registry hay trạng thái kích hoạt cá nhân. Không
cần sửa DLL/giấy phép để đạt kết quả thử nghiệm này.

**Nguồn của lượt đầu:** `Lib/AITalk/aitalk.lic` có sẵn trong MSI gốc và giống
từng byte file đang dùng. Đây không phải file chỉ được tạo khi kích hoạt máy
cá nhân. Tuy nhiên **chưa xác minh nguồn bộ cài của từng `voice.lic`**: MSI
Editor không chứa voicebank hoặc language package, nên các file đó trong
thử nghiệm lấy từ bản đã cài. Chưa kết luận mọi file voice license đều chung
cho mọi khách hàng.

Kết quả chứng minh runtime đang có không phụ thuộc trạng thái kích hoạt của
prefix cũ trong các ca đã chạy. Đây là môi trường Linux/Wine sạch trên cùng
host, chưa phải xác minh trên một máy vật lý/VM thứ hai hay triển khai đầy
đủ addon/installer trên máy khách.

## Nguồn đầu vào

- MSI do người dùng chỉ định:
  `[AUTHOR_HOME]/Downloads/A.I.VOICE2 2.14.1/AIVoice2Editor.msi`.
- Trích xuất bằng `msiextract`, không thực thi installer hay custom action.
- Engine `Lib/AITalk/aitalk_engine.dll` SHA-256:
  `711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17`.
- `aitalk.lic` SHA-256:
  `c7a013e6dabbc143b1fe5352ad38b5f9bd117b7b22abe46911c21b49bfe7004b`.
  Có trong bảng File MSI, entry `filE2CEC20B06718D426EE58359067451F6`.
- Runtime native + giấy phép engine: 42 file, lấy trực tiếp từ MSI. DLL chọn
  theo closure import PE; không đưa Editor, `ailm.dll`, `ailm.exe` hoặc
  `AI.Framework.License.dll` vào runtime thử.
- Hai `.aildic`, chín `.aivdic` canonical và chín `voice.lic`: lấy từ
  `AIVoice2Editor/` đã có trong workspace. Không lấy infox, app settings,
  AppData, registry hoặc file bên ngoài allowlist.
- Tổng 62 file đầu vào runtime/data, 4.434.809.219 byte; chưa tối ưu bundle.
  Probe và worker tự build riêng từ source hiện tại, giữ nguyên auth.

`AI.Framework.License.dll` trong bản đã cài khác hash bản MSI. Test không đưa
cả hai DLL này vào runtime, cũng không dùng hai file DLL đứng cạnh MSI trong
Downloads. Vì vậy kết quả dương tính không dựa vào license manager đó.
Không suy ra nguyên nhân hai phiên bản DLL khác nhau chỉ từ hash.

## Cách cô lập

Script: [tests/clean_runtime_probe.py](../tests/clean_runtime_probe.py).

Bubblewrap dùng mount/user/PID/network/UTS namespace mới, môi trường process
được xóa rồi chỉ thêm PATH, LANG, WINEPREFIX và tùy chọn Wine. `/usr` là read
only để chạy Wine hiện có; `/etc` tối thiểu có machine-id ngẫu nhiên mới.
`/tmp` và `/dev` riêng. Không mount thư mục cá nhân hoặc `/run` của host.

Chỉ bind `/input` read only (allowlist đã chép) và `/work` writable. Assert
prefix chưa tồn tại trước `wineboot --init`; thư mục `.wine-aivoice` và Anki
cá nhân không thấy từ bên trong. `/proc` thuộc PID namespace riêng. Không có
mạng host, không socket desktop, không UI Editor và không chạy activation.
Credentials engine được đọc từ `aitalk.lic` MSI bằng reader đã có, truyền
qua môi trường process con; không lưu plaintext vào log/report.

## Ca thử và quan sát

| Ca thử | Quan sát |
| --- | --- |
| Wineboot trong prefix mới | exit 0 |
| Đường dẫn thiếu engine license | initialize=0, authenticate=-7, exit 5 |
| Có engine license, thiếu voice license | authenticate=0, talker khác NULL, loadVoiceDic=-7, exit 6 |
| Auth với engine license nguyên bản MSI | initialize=0, authenticate=0, talker khác NULL, terminate=0, exit 0 |
| Worker nguyên bản + chín giọng | readiness=0; cả 18 request status=0; exit 0 |
| WAV | PCM int16 mono 48 kHz, đúng số byte trả về, dữ liệu không im lặng |

Câu thử: `です。` và `こんにちは。今日はいい天気ですね。`. Akane dùng Kansai,
Aoi/galaco dùng standard theo bản sửa dialect trước. Với `です。`, Akane NV
có 123840 byte PCM, Aoi NV 115200 byte; hai output khác nhau.

Đối chiếu với evidence runtime trước: bảy voice legacy/galaco khớp từng byte
ở `です。`. NV có cùng độ dài nhưng PCM không hoàn toàn bằng byte; `です。`
sai số tối đa 1 int16, câu dài có sai số lớn hơn. Lưu đầy đủ max delta/RMSE/SNR
trong audit, chưa xác định nguyên nhân chênh lệch số học/môi trường. Không dùng
test sạch này để tuyên bố mọi cấu hình có PCM bit-identical. Việc synth thành
công và không phụ thuộc prefix kích hoạt vẫn được quan sát trực tiếp.

Wine ghi cảnh báo fontconfig và cpuinfo trong môi trường tối thiểu; các ca
auth/synth vẫn exit 0. Chưa xem đây là cấu hình runtime tối ưu để phát hành.

## Evidence và tái lập

- [result.json](evidence/clean-runtime/result.json): kết quả, hash registry
  mới, negative controls, PCM hash và số byte cả 18 mẫu.
- [manifest.json](evidence/clean-runtime/manifest.json): allowlist, nguồn,
  kích thước và SHA-256 từng file đầu vào.
- [installer-comparison.json](evidence/clean-runtime/installer-comparison.json):
  hash MSI, engine/license và so sánh với bản đã cài.
- `msi-File.idt`, `msi-Property.idt`, `msi-extraction.log`: bảng MSI và đường
  dẫn file trích xuất, không chứa license code đã giải mã.
- [isolation-command.json](evidence/clean-runtime/isolation-command.json):
  đầy đủ command cô lập, không chứa credentials.
- [audit.json](evidence/clean-runtime/audit.json): số file, kiểm tra không
  dùng license manager, đối chiếu PCM với runtime trước.
- `run.log`, `wineboot.log`, `worker.log` và log ba control: output thực tế.
- [rea-auth-evidence.json](evidence/clean-runtime/rea-auth-evidence.json):
  REA/IDA auth core tại `0x1800CBA40`, Evidence ID
  `ev_96d18933406a2bad8d41e7bc7671aa14b4d18c31ee70da67a44cf2cb2546c3e4`.
  Phân tích tĩnh thấy luồng đọc license rồi gọi kiểm tra nhận dạng; không
  coi việc thiếu direct-call API mạng ở riêng hàm này là chứng minh offline.
  Bằng chứng offline đến từ namespace runtime của thử nghiệm.

Chạy lại (tạo prefix/input mới mỗi lượt):

```sh
msiextract -C cache/clean-msi-extract '[AUTHOR_HOME]/Downloads/A.I.VOICE2 2.14.1/AIVoice2Editor.msi'
python3 tests/clean_runtime_probe.py
```

MSI extract cần tồn tại tại vị trí script dùng; không trộn file của một
phiên bản khác vào cùng thư mục. Artifacts local của lượt đã qua nằm ở
`cache/clean-runtime-lx1zcdkh/` (có prefix, input và WAV); đây không phải gói
phân phối cho khách. Các script/service/addon production không bị thay đổi
trong lần kiểm tra này, Anki và A.I.VOICE2 gốc không bị đóng/mở lại.

## Bước tiếp theo

1. Đã đối chiếu `.aivdic`, `.aildic` và `voice.lic` công ty cấp cho Akane/Aoi
   NV; chạy được cả Hime/Mikoto mới. Nếu phát hành thêm legacy/galaco thì
   tiếp tục xác nhận nguồn những giọng đó.
2. Tạo bộ cài cầu nối tự dựng prefix mới từ runtime đã xác minh, không ship
   prefix cá nhân. Giữ lời gọi auth nội bộ hiện có; khách không phải nhập
   trường nhận dạng runtime đã nằm trong bộ file đi kèm.
3. Kiểm thử gói đó trên VM/máy thứ hai, gồm tải/cài, offline, Anki phát thử và
   chèn media. Chưa cần chọn phương án patch binary dựa trên kết quả hiện tại.

Tái lập lượt công ty cấp:

```sh
python3 tests/clean_runtime_probe.py --assets-dir '[AUTHOR_HOME]/Downloads/A.I.VOICE2 2.14.1' --report-name company-assets
```

Artifacts riêng: `cache/clean-runtime-c_vlf5gg/`. Trong báo cáo lượt này,
manifest chỉ có origin `original-editor-msi` hoặc `company-supplied-*`;
audit assert không dùng asset từ cây đã cài. Log/WAV vẫn được giữ local.
