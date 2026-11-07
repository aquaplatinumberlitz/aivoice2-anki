# AIVoice2 RE + Anki TTS API

Giao diện hiện tại 0.2.0 dùng Qt 6, thêm nguồn giọng riêng và nghe thử audio:
[MODERN_UI_VI.md](docs/MODERN_UI_VI.md).

Kế hoạch bàn giao tiếp theo: [DELIVERY_PLAN_VI.md](docs/DELIVERY_PLAN_VI.md).
Dev mới bắt đầu tại [DEV_HANDOVER_INDEX_VI.md](docs/DEV_HANDOVER_INDEX_VI.md).
Đã duyệt bàn giao 0.1.0; quyết định bỏ qua các gate còn lại được ghi tại
[user-acceptance.json](release/user-acceptance.json). `PLAN.md` là tên plan
PoC lịch sử; hướng hiện hành nằm trong tài liệu bàn giao ở trên.
Tiến độ thực hiện: [DELIVERY_PROGRESS_VI.md](docs/DELIVERY_PROGRESS_VI.md).
Config portable và công cụ build: [RUNTIME_CONFIG_VI.md](docs/RUNTIME_CONFIG_VI.md).

Copy an toàn của A.I.VOICE2 Editor (Flutter/.NET6 + aitalk_engine.dll) để reverse và wrap thành HTTP API cho Anki Desktop trên Linux.

- `AIVoice2Editor/` — bản copy nguyên vẹn, chỉ đọc, dùng RE tĩnh. Không chạy trực tiếp lên prefix gốc.
- `wineprefix/` — clone runtime riêng cho daemon (tránh tranh app_settings.json với editor gốc)
- `src/daemon/` — daemon Wine P/Invoke engine, expose HTTP
- `src/anki-addon/` — addon Anki: nút 🔊 + dropdown voice tự detect
- `notes/` — kết quả RE (export table, trace)
- `cache/` — WAV cache theo hash

Gốc (không đụng): `~/.wine-aivoice`
License: user sở hữu hợp pháp phần mềm + license.

PoC đã auth, load/select language + voice và synth được WAV. Chạy:

```sh
cd /home/admin/aivoice2-re
python3 src/daemon/run_auth_probe.py --synthesize
```

Output: `cache/probe.wav` (mono PCM 16-bit 48 kHz). Chi tiết nguyên nhân `auth=-3`,
prototype đúng và evidence: [notes/POC_UNBLOCKED.md](notes/POC_UNBLOCKED.md).
`src/daemon/poc.c` cũ chứa các giả định sai; dùng `auth_probe.c` và runner mới.

## Dùng trong Anki

Addon đã cài tại `~/.local/share/Anki2/addons21/aivoice2_local`.
**Đóng/mở Anki một lần** để nạp nút 🎙 và mẫu card mới.

1. Trong Add, chọn loại note **A.I.VOICE2 · Nhật–Việt**. Có bốn field:
   Japanese, Romaji, Vietnamese, Audio. Nhập tiếng Nhật, romaji và nghĩa Việt;
   Audio có thể để trống. Bản này chưa tự dịch hoặc sinh romaji.
2. Khi học, bôi đen đoạn tiếng Nhật → bấm **🎙 Nghe thử** cạnh vùng chọn.
   Hộp thoại mở và phát đúng phần được chọn, có dropdown 9 giọng.
3. Nếu đồng ý, bấm **Đồng ý · Chèn vào card** để lưu WAV vào media và thêm
   `[sound:...]` vào field Audio. Đóng hộp thoại sẽ không sửa note.
4. Trong editor cũng có nút **🎙 AI** / `Ctrl+Shift+V`, lấy phần bôi đen hoặc
   field đang chọn. Hỗ trợ note type hiện có bằng dropdown field đích.
5. **Tools → A.I.VOICE2 — Phát thử…** cho phép nhập bất kỳ câu nào để nghe.

Mặt trước hiển thị tiếng Nhật và nút mở romaji; mặt sau thêm nghĩa Việt và audio.
Không thay template của note type cũ. Audio chỉ phát tự động theo cài đặt Anki
sau khi đã lưu vào card; nút 🎙 hoạt động trên Anki Desktop có addon.

Backend local giữ engine sống, xếp hàng synth và cache WAV:

```sh
systemctl --user status aivoice2-tts
systemctl --user restart aivoice2-tts
journalctl --user -u aivoice2-tts -n 30
```

API: `GET /healthz`, `GET /v1/voices`, `POST /v1/speak {"text":"こんにちは","voice":"KotonohaAkane_ns_48/KotonohaAkane_ns_48"}`.
Tự quét lại voice trên mỗi lần refresh; mỗi request chỉ chọn package có `voice.lic`.
Đã chạy 9 giọng; chưa có control speed/volume/pitch.

Build/cài lại addon: `python3 src/anki-addon/install.py`.
Gói import: `cache/aivoice2-local.ankiaddon`.
Test GUI thật với profile riêng: `/usr/bin/python tests/anki_gui_smoke.py`.
Test editor cũ (Anki có thể dùng mặc định): `/usr/bin/python tests/anki_gui_smoke.py --legacy`.
Addon hỗ trợ cả `Editor` (note trong bộ nhớ) và `NewEditor` (note qua backend),
bao gồm Add và sửa note đã có.
Evidence: `notes/evidence/anki-gui-smoke.jsonl`, `utf8-regression.json`.

**Encoding:** UTF-8 phải truyền `0` vào `ai_Talker_talk`. `1` tạo WAV nhưng đọc
mojibake. Backend đã sửa và tự vô hiệu cache cũ theo hash engine worker.

**Akane/Aoi:** backend chọn Kansai cho Akane, standard cho Aoi theo Editor.
Đã sửa lỗi ép mọi giọng dùng standard khiến hai NV trùng PCM. Test đối chiếu
`です。` với GUI: `python3 tests/voice_dialect_regression.py`.
Chi tiết RE: [notes/VOICE_IDENTITY.md](notes/VOICE_IDENTITY.md).

**Máy mới:** đã kiểm tra engine trích từ MSI gốc trên prefix mới hoàn toàn,
offline, không import kích hoạt/registry cá nhân: cả 9 voicebank tổng hợp được.
Engine `aitalk.lic` có sẵn trong MSI. Đã chạy thêm prefix sạch chỉ dùng MSI và
lang/voicebanks công ty cấp: Akane NV, Aoi NV, Meika Hime NV và Meika Mikoto NV
đều tổng hợp được, không nhập key cá nhân, không patch DLL. Hai Meika mới chỉ
được test riêng, chưa thêm vào addon đang dùng. Phạm vi và bằng chứng:
[notes/CLEAN_RUNTIME.md](notes/CLEAN_RUNTIME.md).

**GUI Free:** bản review thay helper `ailm.dll`, dùng `FreeLicenseManager`
trong framework gốc. Hướng dẫn cơ chế và cách dùng cho người mới:
[notes/FREE_CLIENT_GUIDE_VI.md](notes/FREE_CLIENT_GUIDE_VI.md).
Source: [LicenseAdapter.cs](src/free-client/LicenseAdapter.cs).
