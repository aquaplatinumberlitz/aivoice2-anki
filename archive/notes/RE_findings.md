# RE Findings - aitalk_engine.dll (REA/IDA)

> **Free GUI review (2026-11-06):** helper ailm.dll mới dùng FreeLicenseManager
> với framework stock đã mở GUI sạch/offline, nạp 4 NV và xuất WAV, chỉnh
> speed/pitch/volume. DLL người dùng patch vẫn lỗi WMI trên prefix sạch.
> Chi tiết/phạm vi: [FREE_CLIENT_REVIEW.md](FREE_CLIENT_REVIEW.md).

> **FreeLicenseManager (2026-11-06):** gọi DLL managed gốc xác nhận feature
> enabled/authenticated, Product/Perpetual, không expired, các hạn mức tối đa.
> Chưa xác minh toàn bộ GUI dùng manager đó. [FREE_LICENSE_CAPABILITIES.md](FREE_LICENSE_CAPABILITIES.md).

> **GUI vs headless (2026-11-06):** headless không cần kích hoạt cá nhân nhưng
> API đã thử vẫn cần lic runtime. GUI stock đủ file lic thử tạo license tạm,
> lỗi BrokenWMI trong Wine sạch; bỏ lic lỗi Talker. Chi tiết và giới hạn:
> [GUI_HEADLESS_LICENSE.md](GUI_HEADLESS_LICENSE.md).

> **Môi trường sạch (2026-11-06):** engine/aitalk.lic nguyên bản từ MSI chạy
> offline trong prefix mới, 9 giọng/18 mẫu thành công. Lượt thứ hai chỉ dùng
> MSI + Lang/voicebanks công ty cấp: 4 NV/8 mẫu thành công, gồm Hime/Mikoto.
> voice.lic Akane/Aoi công ty cấp khớp bản đã cài; không cần patch engine.
> [CLEAN_RUNTIME.md](CLEAN_RUNTIME.md) giữ phương pháp, allowlist và evidence.

> **Akane/Aoi NV (2026-11-05):** đã tìm và sửa lỗi ép `standard` cho mọi voice.
> Akane cần Kansai theo Editor. Đối chiếu từng mẫu PCM và tài liệu RE mới:
> [VOICE_IDENTITY.md](VOICE_IDENTITY.md).

> **Đã gỡ kẹt và synth ra WAV (2026-11-05).** Xem [POC_UNBLOCKED.md](POC_UNBLOCKED.md)
> và `src/daemon/run_auth_probe.py --synthesize` cho luồng đã kiểm chứng runtime.
> Các phần dưới là lịch sử điều tra; suy đoán ba đường dẫn auth, wrapper một
> tham số, loadLangDic một tham số, voice license NULL và callback buffer trực
> tiếp đã bị bác bỏ. Không dùng các prototype suy đoán dưới đây để viết code.

- SHA256: 711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17
- PE32+ x86-64, imagebase 0x180000000, 214 ai_ exports, strings_cache 6883

## Export không gian
- ai_Talker_* : object chính (new/newEx/delete, loadVoiceDic/loadLangDic/loadDic, talk/talkByIrText, selectVoiceDic/selectLangDic, getVoiceDicKeys/getLangDicKeys, getVoiceName/Fs/Gender ByKey, setSink, compile/textAnalyze)
- ai_TalkerConfig_* : volume/pitch/rate/emph/pause/masterVolume...
- ai_TtsIrObject_* : IR trung gian
- ai_TtsCallbackSink_* : sink callback (stream WAV ra ngoài)
- ai_PathSet_* : path config
- ai_ttsLibrary* : Initialize/Authenticate/Terminate/Log

## Talker init (suy từ loadLangDic 0x1800c3cf0)
- ai_Talker_loadLangDic(obj) : 1 arg obj; cần byte_1803A62DD !=0 (đã authenticate) else trả -1001
- Lớp gate: mọi load đều check authenticated flag

## loadVoiceDic (0x1800c4420) signature
- ai_Talker_loadVoiceDic(obj, a2, a3, a4, a5):
  - a2, a3: char* không rỗng (key + path)
  - a4: unsigned int (type)
  - a5: int64 (mode?)
- Validate byte_1803A62DD, null obj => trả -3 (4294967293), unauthenticated => -1001
# Semantic (quan sát)
- a2 = key (vd "KotonohaAkane_ns_48"), a3 = đường dẫn .aivdic hoặc folder, a4 = 0/1 (DirPackage/TarFilePackage), a5 = ?
# loadDic (0x1800c3980) chi tiết hơn
- ai_Talker_loadDic(obj, a2, a3, a4, a5): a4=0 => DirPackage (folder), a4=1 => TarFilePackage (.aivdic tar)
- Check package chứa "voice" entry, rồi gọi sub_1800C03E0(a2,a3,a5) để verify? rồi dispatch via vtable +32 / +8
- Vì .aivdic là tar archive (USTAR: METADATA, voice/db.cfg) => TarFilePackage path khi a4=1

## Khám phá thêm cần làm
- [ ] ai_Talker_new / newEx signature (cần decompile)
- [ ] ai_Talker_loadVoiceDicByKey vs loadVoiceDic khác gì (ByKey dùng key đã register?)
- [ ] ai_Talker_talk / talkByIrText : stream ra WAV qua sink hay buffer?
- [ ] ai_TtsCallbackSink_new : callback WAV
- [ ] ai_ttsLibraryInitialize/Authenticate : tham số license
- [ ] sub_1800C03E0 : validator (license?)
- [ ] strings: search "aivdic", "aildic", "voice.lic" trong DLL (chưa parse được do output structure khác)

## Decoded evidence
- ai_Talker_loadVoiceDic @0x1800c4420 ev_728d6febc59971fc68b367a58c827a45331566a976268a8d7f76eec9e56bf39c
- ai_Talker_loadLangDic @0x1800c3cf0 ev_daafd08138caecc5676ba0facdacd06349d568fa37520a95bf8c5c758f048546
- ai_Talker_loadDic @0x1800c3980 ev_5e48dd431a0446504e273c029433b0908c3a1331b658f839234db73b7a69b658
- PROTOTYPE ghi nhận: không claim toàn bộ header C chưa biết

## Decompile bổ sung (2026-11-05, REA/IDA)
- ai_Talker_new @0x1800c45a0: ai_Talker_new() -> ptr 0x10 bytes, sub_1800D3110 init; cần authenticated, null nếu chưa auth
- ai_Talker_talk @0x1800c4930: ai_Talker_talk(obj, a2, a3) -> check is-Talker-ready (sub_1800C05A0) rồi sub_1800E7AE0(obj, a2, a3); a2 có thể là IrObject / text ptr, a3 là uint (offset/flags?) — cần đọc tiếp sub_1800E7AE0
- ai_Talker_setSink @0x1800c4850: ai_Talker_setSink(obj) -> sub_1800E2320(); có vẻ obj + sink global? thực tế cần args thứ 2 (sink obj) mà decompiler optimize bỏ? cần kiểm tra assembly caller
- ai_TtsCallbackSink_new @0x1800c52e0: ai_TtsCallbackSink_new(cb_ptr, cb_ctx) -> vftable ai::TtsCallbackSink; handler null guard
- ai_ttsLibraryInitialize @0x1800c6060: ai_ttsLibraryInitialize(a1) -> sub_1800C6280 init path?, rồi sub_1800C6550 core init
- ai_ttsLibraryAuthenticate @0x1800c5ff0: thunk -> Authenticate_0 @0x1800c6190
- Init order suy: ai_ttsLibraryInitialize -> ai_ttsLibraryAuthenticate -> ai_Talker_new -> setPathSet/SetSink -> loadLangDic -> loadVoiceDic -> talk

## Thiếu
- aitalk_engine.lib 108K chưa giải: strings trong lib có thể chứa header C thật (prototype)
- Cần disasm sub_1800E7AE0 (talk core), sub_1800E2320 (setSink core), ai_Talker_setPathSet @0x1800c47e0, ai_PathSet_add @0x1800c0a30, ai_ttsLibraryAuthenticate_0 @0x1800c6190
- Cần inspect aitalk_engine.lib bằng strings/COFF parsing

## Decompile bổ sung 2
- ai_Talker_setPathSet @0x1800c47e0: ai_Talker_setPathSet(obj) -> sub_1800E2240(); nhưng decompiler bỏ arg PathSet? cần assembly caller — có thể obj chứa pathset bên trong hoặc hàm này lấy từ Talker newEx. Chưa kết luận đủ để code
- ai_PathSet_add @0x1800c0a30: ai_PathSet_add(obj) -> sub_1800CBFE0(); cũng 1-arg như mọi wrapper (vì vtables internal)
- ai_ttsLibraryAuthenticate_0 @0x1800c6190: ai_ttsLibraryAuthenticate_0(path, a2, a3) — 3 char* không rỗng, gọi sub_1800CBA40(a1,a2,a3); log "Engine was Authenticated. path:%s" nếu v6==0. 3 tham số chính là 3 file lic/path (aitalk.lic + voice.lic + ?). Cần tìm caller trong app.so/GUI để biết truyền gì
- ai_Talker_loadVoiceDicByKey @0x1800c4530: chỉ nhận obj, load theo key đã đăng ký trong PathSet (không nhận path trực tiếp). Dùng khi đã add path trước đó
- ai_Talker_talkByIrText @0x1800c4c10: talkByIrText(obj, irTextObj) -> sub_1800E7650(obj, ir)
# Flow suy toàn cục (Init order)
1. ai_ttsLibraryInitialize()
2. ai_ttsLibraryAuthenticate(licPath1, licPath2, licPath3)
3. ai_Talker_new() (hoặc newEx)
4. ai_PathSet_new(); ai_PathSet_add(pathSet, "Lang", langDir); ai_PathSet_add(pathSet, "Voice", voiceDir) ??? (cần decompile sub_1800CBFE0 thêm)
5. ai_Talker_setPathSet(talker, pathSet)
6. ai_Talker_loadLangDic(talker); ai_Talker_loadVoiceDic(talker, key, path, mode, ctx) hoặc loadVoiceDicByKey
7. ai_TtsCallbackSink_new(cb, ctx); ai_Talker_setSink(talker, sink)
8. ai_Talker_talk(talker, irText, 0) / talkByIrText
9. WAV đi qua callback sink

## Assembly xác nhận (không đoán)
- Cả 3 wrapper ai_Talker_setPathSet / setSink / PathSet_add: đều là C shim chỉ nhận 1 arg obj (test rcx, rcx; sub rsp 38h), rồi gọi sub_xxxx core với cùng rcx không có arg phụ. Nghĩa là core lấy arg phụ từ obj bên trong hoặc từ global, hoặc signature thật là 2-arg nhưng wrapper chỉ forward 1? Không — assembly cho thấy wrapper chỉ có 1 param (arg0 __int64). Muốn thêm PathSet vào Talker thì PathSet phải đã gán vào Talker qua newEx? Hoặc setPathSet thật sự là 1-arg (tự lấy PathSet từ engine global). Chưa kết luận đủ để code
- ai_ttsLibraryAuthenticate_0 (path + 2 args) cần tìm implementation sub_1800CBA40 để biết 3 path là gì
- ai_Talker_loadVoiceDicByKey chỉ 1 arg — load theo key đã đăng ký (PathSet có sẵn keys)

## Core decompile sâu (không đoán)
- sub_1800CBA40 (auth core) @0x1800cba40: sub_1800CBA40(a1,a2,a3):
  - a1=path lic chính (đọc LicObject), a2,a3 = user/key?; check "NOEXPIRE" qua v17 lic object; sub_1800C7A40(v17,a2,a3, noExpireFlag)
  - auth ok -> alloc 0xC0 License object, set byte_1803A62DD=1, qword_1803A62D0=obj
  - check "OMIT:CHECK:VOICEKEY" — quan trọng cho voicekey validation
  - => ai_ttsLibraryAuthenticate(path, user, key) — 3 string
- sub_1800CBFE0 (PathSet::add core) @0x1800cbfe0: sub_1800CBFE0() -> sub_1800CBD80(); wrapper ai_PathSet_add chỉ có 1 arg?
- sub_1800E2320 (setSink core) @0x1800e2320: sub_1800E2320(a1_talkerHandle, a2_sink)
  - wrapper ai_Talker_setSink @0x1800c4850 assembly: chỉ test rcx (talker) rồi call sub_1800E2320 với cùng rcx — không có rdx thứ 2? Vậy sink phải nằm trong obj? hoặc wrapper bị export alias gộp? Chưa kết luận đủ để code — cần debug dynamic xem rdx lúc gọi thật
- sub_1800E2240 (setPathSet core) @0x1800e2240: sub_1800E2240(a1_talker, a2_pathSet) tương tự: *(*(a1+8)+240)=a2
  - wrapper cũng 1-arg như setSink -> dấu chấm hỏi Args 2
  - export_ai_Talker_setPathSet trong lib có thể là 2-arg mà REA wrapper bị rút gọn do calling convention? Assembly cho thấy wrapper chỉ dùng rcx, chưa test rdx. Cần dynamic hoặc check .lib COFF header để biết signature C thật
- talk core sub_1800E7AE0 chưa deep dive; talkByIr core sub_1800E7650 chưa deep dive

## Init order tối thiểu
1. ai_ttsLibraryInitialize()
2. ai_ttsLibraryAuthenticate(licensePath, user, key)  — 3 string, vd Lib/AITalk/aitalk.lic
3. talker = ai_Talker_new()
4. pathSet = ai_PathSet_new(); ai_PathSet_add(pathSet, ...) x2 (Lang/Voice)
5. ai_Talker_setPathSet(talker, pathSet) — args chưa chắc
6. ai_Talker_loadLangDic(talker)
7. ai_Talker_loadVoiceDic(talker, key, path, mode, ctx) — a2=key, a3=path .aivdic, a4=0/1, a5=?
8. sink = ai_TtsCallbackSink_new(cb, ctx); ai_Talker_setSink(talker, sink)
9. ir = ai_TtsIrObject_newFromAIKana? hoặc Talker_compile(text) -> ai_Talker_talk(talker, ir, 0)

## Core decomspile 3
- sub_1800E7AE0 (talk core): talk(handle, char* text, uint encoding) log "API called. api:%s this:%p text:%s encoding:%d" rồi sub_1800E5770(handle, text, encoding). Encoding là int (UTF-8/Shift-JIS?). Text là char*.
- sub_1800E7650 (talkByIr core): talkByIr(handle, irObj) -> sub_1800E29C0(handle)
- sub_1800CBD80 (PathSet::add core): sub_1800CBD80(pathset_obj, const char* key, const char* path) — cả 2 char* non-null else -3. Key đầu tiên hay thứ 2? a2 rồi a3: a3 là path string (đã copy vào std::string), a2 là key (vd "Lang"/"Voice"). Thứ tự: sub_1800CBD80(obj, key, path)
- => ai_PathSet_add wrapper thật sự 3-arg nhưng decompiler báo 1-arg do wrapper mỏng và calling convention? Assembly wrapper chỉ test rcx và call core không truyền rdx/r8? Cần check rdx trong wrapper assembly — REA disasm trước chưa có rdx? Chưa tìm ra; để dynamic trace khi chạy PoC
- Ai Takero config: TalkerConfig_new -> setVolume/setPitch/setRate/setMasterVolume trước talk

## Tóm tắt signature suy
- ai_ttsLibraryInitialize() -> 0
- ai_ttsLibraryAuthenticate(const char* licPath, const char* user, const char* key)
- talker = ai_Talker_new()
- pathset = ai_PathSet_new(); ai_PathSet_add(pathset, "Lang", langDir); ai_PathSet_add(pathset, "Voice", voiceDir)
- ai_Talker_setPathSet(talker, pathset)
- ai_Talker_loadLangDic(talker)
- ai_Talker_loadVoiceDic(talker, voiceKey, voicePath, 0, 0) / a4=1 cho .aivdic tar
- sink = ai_TtsCallbackSink_new(cb, ctx); ai_Talker_setSink(talker, sink)
- ai_Talker_talk(talker, textUtf8, encoding)
