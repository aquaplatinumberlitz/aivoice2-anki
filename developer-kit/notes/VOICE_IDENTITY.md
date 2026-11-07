# Akane NV / Aoi NV: lỗi chọn từ điển ngôn ngữ

Kiểm chứng ngày 2026-11-05, engine SHA-256
`711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17`.

## Kết luận và bản sửa

Addon chọn đúng voice package, nhưng worker luôn chọn ngôn ngữ `standard`.
Editor dùng **Kansai cho Akane, standard cho Aoi**. Mất phần phân tích Kansai
làm hai NV trùng PCM trong các thử nghiệm trước. Không thể suy từ đó rằng
Editor thật phát hai giọng giống nhau.

`server.py` gửi cả language key/package theo voice; `engine_worker.c` đổi
ngôn ngữ độc lập với voice. Cache có language, mtime language package và hash
worker mới nên bỏ qua audio của bản lỗi. Không sửa model/license, không ép
emotion để tạo khác biệt. Không sửa hay khởi động lại A.I.VOICE2 gốc.

Mapping: `KotonohaAkane_ns_48`, `akane_west_emo_48`, `akane_west_mini_48`,
`akane_west_syou_48` dùng Kansai; Aoi và galaco dùng standard. Voice mới vẫn
được phát hiện tự động nhưng dialect sản phẩm mới cần xác minh riêng.

## Bằng chứng runtime

[Ảnh cửa sổ gốc](ARCHIVE_COVERAGE.md) xác nhận người dùng test
đúng hai NV với `です。`. Engine, hai voice package và hai language package
giữa bản gốc/bản copy có hash khớp:
[artifact-identity.json](evidence/voice-identity/artifact-identity.json).

GUI copy chạy prefix/Xvfb riêng, DLL proxy forward nguyên lời gọi tới engine
thật. Tạo block mới riêng cho từng NV, nhập `です。`, thu PCM tại BUFDONE:

| Giọng/dialect | Accent ImKana của GUI | PCM bytes | 48 kHz |
| --- | --- | ---: | ---: |
| Aoi NV / standard | accentUp=1, accentDown=1 | 115200 | 1,20 s |
| Akane NV / kansai | accentUp=2, accentDown=0 | 123840 | 1,29 s |

Cả hai có cùng mora デ/ス, style `J:0,A:0,S:0,C:0`, pitch/rate 1.
GUI masterVolume=1,06; worker mặc định=1. Nhân mẫu worker với 1,06 rồi làm
tròn: sai số GUI tối đa **1 đơn vị int16** cho cả hai, RMSE khoảng 0,0543
(Aoi) và 0,0607 (Akane). Đây là so từng mẫu, không chỉ xem hash khác nhau.

Bằng chứng để tái sử dụng:

- [gui-calls.txt](evidence/voice-identity/gui-calls.txt): voice, config, JSON
  ImKana và selectLangDic (bổ sung wrapper ở lượt trace sau).
- [gui-dialect-map.json](evidence/voice-identity/gui-dialect-map.json): chọn
  Kansai cho Akane NV, standard cho Aoi NV và các nhân vật khác. Lượt trống
  vì cache/debounce không phải quan sát trực tiếp về lựa chọn của lượt đó.
- `desu-gui-KotonohaAkane_ns_48.pcm`, `desu-gui-KotonohaAoi_ns_48.pcm`:
  PCM GUI s16le mono 48 kHz.
- [dialect-desu.json](evidence/voice-identity/dialect-desu.json): thử cả hai
  dialect trên cả hai voice. Cùng dialect thì NV trùng PCM ở câu này.
- [desu-gui-comparison.json](evidence/voice-identity/desu-gui-comparison.json):
  so worker dialect đúng với GUI.
- [dialect-regression.json](evidence/voice-identity/dialect-regression.json):
  API sau sửa, ba câu, đổi dialect, cả 9 giọng và cache.
- `gui-trace-proxy.c`, `gui-trace-proxy.def`: source proxy để tái lập.
  `aitalk_real.dll` phải là copy thực; symlink có thể khiến Wine bỏ qua proxy.

Test: `python3 tests/voice_dialect_regression.py` khi service chạy.
Anki GUI test với NewEditor/profile tạm riêng đã qua: phát thử không sửa
note/media, đồng ý chèn được audio, không lặp tag và giữ các field khác.
Log: [anki-gui-smoke.jsonl](evidence/anki-gui-smoke.jsonl).

## Phát hiện RE cho lần phục dựng sau

- Hai `.aivdic` là tar; featnet/vocoder/postprocessor và nhiều member chung.
  `speaker.json` có tên khác nhau nhưng index 1 trong cả hai. Style mapping
  D=平静, C=蕾, J=喜び, S=悲しみ, A=怒り. Vector D bằng nhau, C/J/S/A khác.
  Xem [package-comparison.json](evidence/voice-identity/package-comparison.json).
- `ai_TalkerConfig_setStyleColor(config, const char*)` dùng `C:1`, không phải
  `C=1` hay chỉ `C`. Probe C/J tạo hai PCM khác nhau. Đây là định dạng ABI
  đã thử, không phải bản sửa lỗi dialect.
- `ai_Talker_getDefaultConfig(talker)` trả con trỏ mượn, không tự delete.
- Editor synth `ai_TtsImKana_newFromJson` → `talkByImKana`; JSON giữ mora,
  accent, volume/rate/pitch/emphasis/style. Không được bỏ qua bước tạo accent
  khi đối chiếu voice. Phân tích tĩnh lưu trong
  [rea-voice-style.json](evidence/voice-identity/rea-voice-style.json).
  Bundle cuối phiên: [rea-final-evidence.json](evidence/voice-identity/rea-final-evidence.json),
  snapshot: `evidence/voice-identity/rea-analysis-snapshot.json` (11 records).
- ABI auth, UTF-8, loaders và callback đúng:
  [POC_UNBLOCKED.md](POC_UNBLOCKED.md).

## Đính chính và giới hạn

Trace trước dùng `hello world`, kéo đổi nhân vật trên cùng block; PCM NV bằng
nhau ở mẫu đó, kể cả GUI copy. [comparison.json](evidence/voice-identity/comparison.json)
chỉ áp dụng cho mẫu đó. Kết luận trước “hai NV mặc định luôn giống nhau” sai;
báo cáo `です。` của người dùng là phản chứng và đã dẫn tới lỗi dialect.

PCM lấy từ GUI copy có artifact hash khớp bản gốc. Cửa sổ gốc chỉ được chụp
ảnh/kiểm tra module và artifact, không hook hay thu PCM trực tiếp. Một số câu
có thể vẫn bằng PCM khi ngữ điệu trung tính trùng nhau; không ép cảm xúc để
bắt mọi câu phải khác. Phục dựng engine vẫn ngoài phạm vi hiện tại.
