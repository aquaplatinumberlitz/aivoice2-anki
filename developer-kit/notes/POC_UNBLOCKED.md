# PoC đã chạy được — 2026-11-05

Đã kiểm chứng runtime bằng Wine trong prefix riêng `wineprefix/`:
`initialize=0`, `authenticate=0`, talker khác NULL, load/select language và
voice đều `0`, `setSink=0`, `talk=0`, `terminate=0`, process exit `0`.

## Chạy lại

Từ `[WORKSPACE]`:

```sh
python3 src/daemon/run_auth_probe.py
python3 src/daemon/run_auth_probe.py --dictionaries
python3 src/daemon/run_auth_probe.py --synthesize
```

Runner build bằng MinGW với `-Wall -Wextra -Werror`, dùng prefix clone riêng,
load DLL theo đường dẫn tuyệt đối, xác minh SHA256 engine/license trước khi
đọc hai trường nhận dạng trong license hiện có. License code chỉ được truyền
qua environment của process con; không hardcode hoặc ghi ra log. Không sửa
DLL/license, không thay đổi activation/expiry. Không chạy editor gốc.

`cache/probe.wav`: câu `こんにちは、世界。`, giọng `KotonohaAkane_ns_48`,
PCM signed 16-bit little endian, mono 48 kHz, 123.210 samples, 246.420 byte PCM,
thời lượng 2,567 giây (đã tạo lại với UTF-8 encoding `0`). WAV header, độ dài, sample rate và dữ liệu không im lặng
đã kiểm tra bằng Python `wave`; xem `evidence/wav-validation.json`.
Chưa đối chiếu âm thanh hoặc byte-for-byte với WAV từ GUI.

## Những giả định sai gây kẹt PoC cũ

1. `ai_ttsLibraryAuthenticate(path, licenseCode, productName)`.
   `path` là `Lib/AITalk/aitalk.lic`; productName là `AIVOICE2`.
   Hai chuỗi rỗng làm wrapper trả `-3` (invalid argument) **trước** kiểm tra
   license. `ai_Talker_new` trả NULL vì flag authenticated vẫn bằng 0.
   Đây không phải bằng chứng Wine không hỗ trợ activation.
2. Wrapper không ghi vào RDX/R8 trên nhánh thành công: đối số ở các register
   này vẫn tới callee. Pseudocode chỉ hiện một tham số là thiếu prototype,
   không phải bằng chứng hàm chỉ nhận một đối số.
3. `ai_Talker_loadLangDic(talker, key, packagePath, packageType)` có **4** đối số.
   Đã dùng key `standard`, `Lang/standard/standard.aildic`, type `1` (tar).
4. `ai_Talker_loadVoiceDic(talker, key, packagePath, packageType, voiceLicensePath)`.
   Đã dùng `Voice/KotonohaAkane_ns_48/KotonohaAkane_ns_48.aivdic`, type `1`,
   đối số cuối là `Voice/KotonohaAkane_ns_48/voice.lic`, không phải NULL/context.
5. Gọi `selectLangDic` và `selectVoiceDic` bằng key sau khi load thành công.
   Luồng đã chạy không cần PathSet.
6. `ai_TtsCallbackSink_new(handler, context)`, với handler
   `int handler(void *context, Event *event)`.
   `Event` là `{ uint32_t type; padding; void *data; }`, tổng 16 byte trên x64.
   Event `3` (BUFREQ) yêu cầu caller cấp buffer, event `4` (BUFDONE) trả dữ liệu.
   `data` ở hai event đó trỏ tới `{pcmPtr, byteCount, markerPtr, markerCount}`,
   bốn trường 64-bit. BUFREQ dùng số lượng làm capacity; BUFDONE dùng actual size.
   Mỗi marker chiếm 80 byte. Các event khác trả `0` để tiếp tục.
   Callback nhận PCM thô; caller tự viết WAV header, không fwrite event thành WAV.
7. **Sửa encoding 2026-11-05:** `ai_Talker_talk(talker, textUtf8, 0)`.
   Lần đầu truyền `1` chỉ tạo được WAV nhưng đọc sai nội dung (mojibake).
   Sau sửa, `こんにちは` trả AIKana `<S>コ^ンニチワ<F>`, audio 1,645 giây.
   Evidence hồi quy: `evidence/utf8-regression.json`.
   `ai_Talker_getVoiceFs` trả `48000`; probe không đoán sample rate.
8. Engine phụ thuộc `c10.dll`, `torch_cpu.dll`, `onnxruntime.dll`, VC runtime...
   Probe load bản `AIVoice2Editor/aitalk_engine.dll` cùng SHA256 với bản trong
   `Lib/AITalk/`, có dependency nằm cạnh. Load riêng DLL trong `Lib/AITalk/`
   không thêm search directory dẫn đến lỗi loader `126`.

`src/daemon/poc.c` và `.exe` cũ được giữ nguyên phần implementation để tham khảo;
chúng chứa các giả định đã bị bác bỏ, không dùng làm điểm xuất phát.
Implementation đã kiểm chứng nằm ở `src/daemon/auth_probe.c`.

## Evidence và bước tiếp theo

- `evidence/auth-probe.txt`: auth + tạo/xóa talker.
- `evidence/dictionary-probe.txt`: load/select language và voice.
- `evidence/synthesis-probe.txt`: synth + số lần nhận từng callback.
- `evidence/rea-engine-20261105.json`: evidence tĩnh REA/IDA, engine SHA256
  `711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17`.
- `evidence/auth-static-20261105.json`: giữ đầy đủ evidence auth/decoder từ
  session trước khi đổi quyền sandbox.
- Guard auth: `0x1800C6190`; auth core: `0x1800CBA40`; so sánh hai trường:
  `0x1800C7A40` (arg3 so product ở offset 0, arg2 so code ở offset 32).
- Decoder license hiện có: `0x1800CAEA0`, `0x1800C6F70`, `0x1800C6AE0`;
  trường độ dài thập phân: `0x1800C8960`, `0x1800C9370`.
- Language loader core: `0x1800DE2A0`; voice license: `0x1800C03E0`, `0x1800CB710`.
- Callback trampoline: `0x1800C0590` giữ RDX và thay RCX bằng context.
- BUFREQ: `0x1800D1EF0`; BUFDONE: `0x1800D1530`; marker stride: `0x1800D1630`.

Đã có engine worker giữ talker sống, text/voice input, HTTP và addon Anki;
xem README. Giữ kiểm tra activation
voice ở tầng sản phẩm khi triển khai; probe này mới xác nhận tầng engine với
voice/license đã có. Chưa kiểm chứng voice khác, thread safety hay hot reload.
