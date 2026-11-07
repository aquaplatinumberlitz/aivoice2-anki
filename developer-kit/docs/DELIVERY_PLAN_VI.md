# Kế hoạch bàn giao A.I.VOICE2 + Anki

Ngày lập: 2026-11-06. Trạng thái: **đã duyệt bàn giao 0.1.0 với các giới hạn
được ghi nhận**. Tài liệu này điều phối công việc bàn
giao tiếp theo; `../PLAN.md` giữ lịch sử PoC/backend/addon trước đó.

Cập nhật nghiệm thu: người dùng đã duyệt bàn giao 0.1.0, bỏ qua nghiệm thu
máy khách/loa thật và hoãn hoàn thiện update/uninstall trong đợt này. Các
checkbox còn mở bên dưới giữ nguyên để thể hiện đúng phần chưa làm;
không dùng chúng để chặn đợt bàn giao đã duyệt. Xem
[user-acceptance.json](../release/user-acceptance.json).

Tiến độ triển khai P0/P1: [DELIVERY_PROGRESS_VI.md](DELIVERY_PROGRESS_VI.md).
Config và công cụ hiện có: [RUNTIME_CONFIG_VI.md](RUNTIME_CONFIG_VI.md).
Hướng mở rộng vntext và API nhiều client:
[TTS_CLIENTS_ROADMAP_VI.md](TTS_CLIENTS_ROADMAP_VI.md).

## 1. Kết quả phải bàn giao

Khách nhận một bộ tích hợp sạch, dùng MSI và các gói Lang/voicebank được
cung cấp riêng. Khách chọn nguồn, chọn giọng và bấm cài; không tự patch DLL,
biên dịch source, sửa service hoặc nhập đường dẫn backend. Sau cài có GUI
để chỉnh/phát/xuất audio và addon Anki để nghe thử/chèn WAV khi đồng ý.

Cùng phiên bản phát hành phải có **bộ hỗ trợ phát triển đi kèm cho khách**:
source, tool, hướng dẫn build, cơ chế RE, evidence đã làm sạch và runbook.
Dev mới có thể đọc theo thứ tự, tái tạo bản build, chẩn đoán lỗi trên máy
khách và khôi phục bản cũ mà không cần máy nghiên cứu của tác giả.

Phạm vi đầu tiên: Linux x86-64 + Wine + Anki Desktop; chốt phiên bản Wine,
distro và Anki thực tế qua ma trận kiểm thử trước khi ghi nhãn hỗ trợ.
Windows native là đợt riêng, chưa có kết quả kiểm chứng tương đương.
Không phục dựng toàn bộ engine, không thêm dịch/romaji tự động hoặc điều
khiển speed/pitch/volume cho API Anki trong đợt bàn giao này.

## 2. Quyết định bố trí đã chốt

- **Một thư mục ứng dụng A.I.VOICE2 làm nguồn dữ liệu duy nhất.** Giọng đặt
  tại `<app>/Voice/`, ngôn ngữ tại `<app>/Lang/`. GUI và backend cùng đọc
  các thư mục đó; không tạo thêm kho voicebank độc lập cho Anki.
- MSI gốc 2.14.1 đã kiểm tra không chứa Lang/voicebank. Chọn nguồn MSI và
  nguồn dữ liệu riêng; chỉ cài các giọng khách chọn. Không giả định cài MSI
  xong là đủ Lang. Nếu Lang tương thích đã có thì giữ nguyên.
- Mặc định tạo app và Wine prefix sạch do trình thiết lập quản lý. Không
  clone prefix cá nhân. GUI và worker có thể dùng prefix riêng để tránh
  xung đột settings, nhưng cùng đọc một app/Voice/Lang.
- Nếu khách có bản A.I.VOICE2 đang dùng: nhận diện và giải thích trước khi
  đụng tới. Đợt đầu ưu tiên cài bản tích hợp riêng, giữ nguyên bản cũ;
  không âm thầm sửa app/prefix khác hoặc import trạng thái kích hoạt.
- Bộ tích hợp mang helper/worker đã biên dịch cùng patcher đúng phiên bản;
  compiler và công cụ RE chỉ thuộc bộ dev, không phải yêu cầu cho khách.
- Framework license, engine và `.lic` runtime dùng đúng bộ đã kiểm chứng.
  Không đóng gói key, activation cá nhân hoặc sidecar DLL đã patch thủ công
  cạnh MSI trong Downloads.
- GUI dùng `ailm.exe` stock chạy helper `ailm.dll` do mình build, chọn
  `FreeLicenseManager` trong framework stock; UI dùng snapshot đã patch.
  Headless gọi engine trực tiếp, không cần GUI/helper đang mở. Các file
  `.lic` runtime đi kèm vẫn cần được giữ, khác với activation cá nhân.
- Nhãn thẻ giọng giữ **Full version**. Patch UI ẩn Deactivate/hướng dẫn và
  chặn callback. Không coi nhãn này là bằng chứng mọi chức năng đã qua QA.

Ví dụ layout trên máy khách, đường dẫn thực tế do trình thiết lập sinh:

```text
<managed-root>/
  app/                    # thư mục cài A.I.VOICE2
    aivoice.exe
    ailm.exe
    ailm.dll
    AI.Framework.License.dll
    data/app.so
    Lang/{standard,kansai}/
    Voice/<voice-id>/      # nguyên thư mục giọng đã chọn
  runtime/                # backend và worker đã build
  prefixes/{gui,engine}/   # tạo mới tại máy khách
  manifests/              # file/version/hash, dữ liệu cài, lịch sử update
  backups/                # file bị thay, thông tin rollback
```

Config, log, cache đặt theo XDG của tài khoản hiện tại. Cấu hình chỉ có
một `app_dir` chuẩn để suy ra Voice/Lang/engine; không hardcode
`/home/admin/aivoice2-re`. Worker, service và launcher cùng dùng config này.

## 3. Hiện trạng và phần thiếu

| Hạng mục | Hiện có | Cần làm để bàn giao |
| --- | --- | --- |
| Engine/headless | Chạy sạch/offline bằng file runtime đi kèm | Tham số hóa đường dẫn, worker build sẵn, test từ gói phát hành |
| GUI | Helper `.3` + patch UI `2.14.1-free-ui.1` đã test sạch | Tích hợp áp patch/sao lưu/rollback tự động, kiểm tra các menu activation còn lại |
| Dữ liệu | Bốn NV công ty cấp đã test sạch | Chọn/cài/gỡ từng giọng; kiểm tra Lang và metadata giọng |
| Anki | Nghe thử, lựa chọn giọng, chèn có xác nhận, editor cũ/mới | Cài portable, bảo toàn config, nối backend từ cùng app_dir |
| Build | Có source helper, C worker và patcher | Bỏ đường dẫn SDK cố định, ghi toolchain, build trên môi trường mới |
| Thiết lập | Có wizard và core staging, init prefix, quản lý giọng | Hoàn thiện updater/uninstall và QA sự cố rộng hơn |
| RE/docs | Có báo cáo, source probe và evidence | Chỉ mục nhập môn, runbook, sửa hướng dẫn lỗi thời, export sạch |
| Phát hành | Đang đóng gói candidate local và dev-kit | QA máy độc lập/loa thật và phê duyệt bản bàn giao |

P1 đã tách runtime config, build worker trước, renderer service và cài addon
theo đường dẫn chọn. Fallback workspace chỉ giữ cho service nghiên cứu cũ;
release launcher dùng config tường minh. `poc.c` cũ có giả định sai, chỉ
giữ trong dev archive; không cài vào runtime khách.

## 4. Các giai đoạn và tiêu chí hoàn thành

### P0 — Chốt baseline có thể tái tạo

- [x] Lập manifest input stock: MSI, framework, snapshot GUI, engine, Lang,
  từng gói giọng; ghi nguồn, phiên bản, kích thước và SHA-256.
- [x] Chốt danh sách ứng viên ban đầu từ các gói công ty cấp. Giọng legacy
  từng chạy từ bản đã cài được ghi riêng, không tự đưa vào release.
- [ ] Chốt distro/kiến trúc, Wine, Anki/editor và cách cung cấp dependency.
- [x] Kiểm tra build hiện tại không cần trạng thái activation của máy dev.

Đầu ra: `release-inputs.json`, bảng tương thích và hướng dẫn lấy đúng input.
Hash kiểm tra tương thích, không ràng buộc theo máy khách. Có thể mở rộng
manifest sau khi một phiên bản mới được nghiên cứu/kiểm thử.

### P1 — Thống nhất config và build portable

Phụ thuộc P0.

- [x] Bổ sung config có version/schema; dùng app_dir chung, runtime dir,
  prefix dir, cache/log dir và endpoint loopback. Có thông báo lỗi dễ hiểu.
- [x] Backend/probe/launcher/service lấy đường dẫn từ config/CLI; production
  không tự gọi compiler khi khởi động. Tạo worker đã build cho release.
- [x] Thay danh sách Kansai hardcode bằng registry giọng có cấu hình dialect
  đã xác minh. Giọng chưa rõ dialect không âm thầm coi là đúng standard.
- [x] Build helper/worker/addon bằng toolchain có phiên bản ghi lại; chỉnh
  build script không phụ thuộc SDK hoặc checkout tại máy tác giả.
- [x] Quản lý service theo tài khoản, bind loopback; phát hiện cổng bị chiếm,
  chỉ khởi động/dừng process thuộc bản cài này.
- [x] Kiểm chứng GUI và worker cùng đọc app/Voice/Lang nhưng không ghi đè
  settings của nhau khi chạy đồng thời.
- [x] Giữ core TTS độc lập Anki và tài liệu contract `/v1/speak`; ghi giới
  hạn scheduler hiện tại và đường mở rộng client vntext theo roadmap P8.

Đầu ra: runtime build sẵn, config mẫu và lệnh build dev có thể tái chạy.
Đạt khi chuyển sang username/đường dẫn có dấu và khoảng trắng vẫn chạy,
không cần sửa source hoặc có `/home/admin` trên máy mới.

### P2 — Trình thiết lập lần đầu

Phụ thuộc P1. Dùng một entry point có giao diện cho khách; không chọn
framework UI mới trước khi kiểm tra dependency có sẵn và khả năng đóng gói.

1. Chào mừng, mô tả ngắn những thành phần sẽ được cài.
2. Chọn MSI; kiểm tra đúng input/phiên bản hỗ trợ trước khi thay file.
3. Chọn `voicebanks/` hoặc gói giọng; tìm `Lang/` cạnh đó nếu có, nếu thiếu
   thì cho chọn riêng. Hiện danh sách giọng và dung lượng cần cài.
4. Tóm tắt vị trí app, giọng đã chọn và tích hợp Anki; khách bấm Cài đặt.
5. Stage bộ stock bằng cách cài/trích MSI đã được kiểm chứng. Quy định rõ
   file native phụ trợ cần có trong layout (gồm engine cạnh dependencies).
6. Tạo prefix mới, bổ sung Lang thiếu, chép nguyên các thư mục giọng đã chọn
   vào app/Voice; giữ `.aivdic`, `voice.lic`, `infox.bin`, `images.dat` nếu có.
7. Sao lưu và áp helper/UI patch đúng hash, xác minh output rồi commit.
8. Tạo launcher/service/config; kết nối addon như P4.
9. Test backend, phát câu mẫu và báo từng thành phần Sẵn sàng/Chưa sẵn sàng.

- [x] Preflight dung lượng, quyền ghi, dependency, nguồn thiếu hoặc sai.
- [ ] Stage trước, commit sau; lỗi/hủy/mất điện có nhật ký giao dịch để
  resume hoặc rollback. Chạy lại setup không nhân đôi giọng/service/addon.
- [x] Bản GUI đang mở không bị kill mất nội dung; yêu cầu lưu/đóng tại bước
  cần cập nhật. Không dùng `wineserver -k` trên prefix ngoài quyền quản lý.
- [ ] ZIP/thư mục được kiểm tra cấu trúc; không giải nén đường dẫn thoát
  staging hoặc theo symlink ra ngoài nơi cài. Gói dữ liệu không tự chạy code.
- [ ] Tách dependency tải mạng lần đầu khỏi việc chạy offline sau cài;
  ghi rõ yêu cầu mạng. Chuẩn bị tùy chọn dependency offline theo distro đã QA.

Đầu ra: một luồng cài GUI + TTS hoạt động dù chưa có Anki; không có bước
copy DLL/build thủ công trong quickstart khách.

### P3 — Quản lý giọng, cập nhật và khôi phục

Phụ thuộc P2; hoàn tất trước release.

- [x] Thêm giọng: chọn nguồn → chọn từng giọng → kiểm tra tương thích/Lang
  → stage → test tổng hợp → đưa vào app/Voice → cập nhật danh sách.
- [ ] Gói trùng: phân biệt đã có cùng hash và cập nhật khác phiên bản;
  không chép đè âm thầm hoặc chỉ dựa vào tên thư mục.
- [x] Gỡ giọng: dừng công việc đang dùng giọng, cảnh báo preset/default liên
  quan, chuyển thư mục ra vùng backup bên ngoài Voice. Giữ preset để khôi
  phục; xử lý lựa chọn giọng đã mất trong GUI/addon bằng hướng dẫn rõ ràng.
- [x] Không hứa hot reload trước kiểm chứng; ban đầu dùng stop/reload/restart
  worker có kiểm soát để tránh DLL/dictionary đang được giữ mở.
- [x] GUI mở lại để quét giọng; addon Refresh lấy danh sách mới. Nếu xóa
  default thì chọn giọng còn lại hợp lệ; không gửi ID cũ vô hạn.
- [ ] Cập nhật app/patch/backend/addon độc lập có manifest tương thích và
  rollback; giữ Lang đã cài nếu phù hợp, chỉ thay theo quyết định rõ ràng.
- [ ] Gỡ bộ tích hợp: chỉ xóa thành phần do setup quản lý; cho chọn giữ lại
  giọng/settings/backup. Không xóa Anki collection hoặc media đã chèn.

Đầu ra: Thêm giọng, Gỡ giọng, Sửa cài đặt, Kiểm tra, Khôi phục, Gỡ tích hợp.

### P4 — Cài và nối addon Anki

Phụ thuộc P1/P2; có thể triển khai sau luồng GUI cài mới.

- [ ] Phát hiện Anki có sẵn và vị trí addon thực tế; hỗ trợ lựa chọn thủ
  công khi bản portable/custom chưa tự phát hiện được. Chỉ ghi nhãn hỗ trợ
  cho dạng cài đã test; Flatpak có boundary riêng cần xử lý và QA trước.
- [x] Khi Anki đang chạy, hướng dẫn lưu/đóng rồi tiếp tục; không kill.
- [x] Cài/upgrade thư mục addon riêng, sao lưu/bảo toàn cấu hình khách;
  cấu hình endpoint từ bản cài này. Cung cấp `.ankiaddon` làm cách cài dự phòng.
- [x] Chưa có Anki: hoàn thành GUI/TTS trước, cho tích hợp Anki về sau.
- [x] Giữ hành vi nghe thử không sửa note; chỉ thêm media/tag khi khách
  đồng ý. Bảo toàn note type cũ, field đích và cấu hình cá nhân.
- [x] Kiểm tra editor cũ/mới, Add/sửa note/reviewer và nhiều profile phù hợp.
- [x] Thông báo rõ: backend tạo audio trên Desktop; audio đã lưu có thể
  sync/phát như media Anki. Không hứa nút mic Desktop chạy trên điện thoại.

Đầu ra: khách không nhập URL/path; mở lại Anki là dùng được. Tài liệu có
phần cài `.ankiaddon` thủ công khi phát hiện tự động không hỗ trợ.

### P5 — Bộ docs, RE, source và tool cho khách/dev hỗ trợ

Khởi đầu từ P0, chốt sau P4. Chỉ mục hiện có:
[DEV_HANDOVER_INDEX_VI.md](DEV_HANDOVER_INDEX_VI.md).

- [x] `START_HERE_VI.md`: sơ đồ thư mục bàn giao, cách cài trong vài bước,
  thêm/gỡ giọng, lấy hỗ trợ; không yêu cầu đọc RE để sử dụng.
- [x] `SUPPORT_RUNBOOK_VI.md`: bảng triệu chứng → kiểm tra → xử lý → kết
  quả mong đợi → cách khôi phục; ghi giới hạn của mỗi công cụ.
- [x] `ARCHITECTURE_VI.md`: GUI/helper/framework/native engine/backend/Anki,
  một app/Voice/Lang, file nào đọc/ghi và khác nhau giữa hai lớp license.
- [x] `BUILD_AND_REPRODUCE_VI.md`: toolchain, source input, lệnh build từ
  checkout sạch, hash mong đợi, lệnh test có đầu ra mẫu và clean-up.
- [x] `RE_FINDINGS_INDEX_VI.md`: mỗi kết luận có binary hash/version,
  offset/symbol/prototype nếu có, Evidence ID hoặc file bằng chứng, trạng
  thái quan sát/suy luận/chưa biết và ngày kiểm chứng gần nhất.
- [x] `UPDATE_ROLLBACK_VI.md`: update tương thích, version không hỗ trợ,
  backup/khôi phục patch và hồi quy cần chạy khi đổi binary/voice/Anki.
- [ ] `CHANGELOG.md`, bảng tương thích, inventory thành phần/nguồn và manifest
  của release; tách chức năng đã test khỏi giả định/lộ trình.
- [ ] Đi kèm source helper/patcher, backend/worker/API header, addon, setup,
  tests/probe còn hiệu lực; tool build/test/diagnostic/export-support dùng được.
- [x] Đưa source probe/proxy tự viết đang nằm trong thư mục build hoặc
  evidence về cây source/tools có quản lý, giữ link provenance; không để
  thao tác dọn build vô tình xóa source độc nhất. Generated output tách riêng.
- [ ] Mang các báo cáo RE hiện có và evidence cần thiết; lưu nguyên lịch sử
  kỹ thuật trong mục archive có chú giải chỗ sai/đã thay thế. Không gọi
  decompile là source gốc, không yêu cầu cài REA/IDA để chạy sản phẩm.
- [x] Tool RE bên thứ ba chỉ ghi phiên bản/cấu hình/cách lấy, không gộp
  phần mềm proprietary/toolchain từ máy dev. Source tool/proxy tự viết
  phải nằm trong bộ dev có hướng dẫn chỉ chạy trên bản thử cô lập.
- [ ] Dev mới làm bài thực hành: build từ input sạch → tổng hợp mẫu đúng
  giọng → tái hiện thiếu Lang → chẩn đoán → sửa → rollback UI patch.

Runbook tối thiểu phải bao phủ: service không chạy/cổng bận; GUI mở lỗi;
voice không hiện; thiếu/sai Lang hoặc voice.lic; auth -3/talker NULL;
こんにちは đọc sai do encoding; Akane/Aoi giống do dialect; addon không kết
nối; Editor/NewEditor; preview sai câu; không ghi được media; cài dang dở;
patch sai version; giọng đã gỡ; chọn nhầm sound device.

### P6 — Đóng gói sạch và công cụ lấy thông tin hỗ trợ

Phụ thuộc P1–P5.

- [ ] Đóng gói bằng allowlist từ source/build/input đã chốt, không zip cả
  workspace `cache/`, `wineprefix/`, bản installed copy hay home tác giả.
- [ ] Loại activation/key cá nhân, registry/prefix có sẵn, lịch sử, collection,
  media/card thật, đường dẫn máy tác giả trong config đang hoạt động và log
  chứa văn bản khách. Giữ đúng `.lic` runtime đi kèm bộ được cung cấp.
- [ ] Evidence chia thành bộ đã làm sạch dùng cho dev và bản nghiên cứu
  nội bộ giữ nguyên. Ảnh desktop/log cá nhân không tự động lọt vào release.
  Giữ provenance/hash binary; nếu làm sạch evidence ghi rõ đã biên tập,
  mapping ID/path và checksum mới, không giả là raw capture nguyên bản.
- [x] `diagnose` kiểm tra read-only: phiên bản, manifest, đường dẫn chuẩn,
  file cần có, service/API, giọng/Lang; mẫu tổng hợp là bước kiểm tra riêng.
- [x] `export-support` tạo ZIP cục bộ có preview nội dung và redaction mặc
  định; không chứa raw license/activation, câu học hay collection. Khách
  chủ động gửi file, không tự upload/email/telemetry.
- [x] Tạo checksum, manifest file đầy đủ, phiên bản config/protocol và
  công cụ xác minh. Bundle runtime và dev phải cùng release ID.

Đầu ra dự kiến (tên chỉ là quy ước, chưa tồn tại):

```text
handover-<version>/
  START_HERE_VI.md
  client-linux-x86_64/     # setup/manager + runtime build sẵn
  anki/aivoice2-local.ankiaddon
  developer-kit/          # giao kèm khách
    START_HERE_DEV_VI.md
    src/ tests/ tools/
    docs/ re-reports/ evidence/ archive/
    toolchain-versions.json
  release-manifest.json
  SHA256SUMS
  CHANGELOG.md
```

MSI và `Lang/voicebanks/` được bàn giao/tải riêng theo quyết định đã chốt;
quickstart chỉ rõ cách chọn chúng. Không nhúng thêm bản binary thử hoặc các
bản DLL framework patch lịch sử vào payload production.

### P7 — Kiểm thử nghiệm thu và bàn giao

Phụ thuộc toàn bộ P0–P6. **Chạy từ bundle đóng gói**, không chạy từ workspace
đang có build/cache/prefix. Mỗi ca ghi version, input hash, môi trường và kết quả.

| Nhóm | Ca bắt buộc | Điều kiện đạt |
| --- | --- | --- |
| Máy mới | User/home mới, prefix mới, không mount máy tác giả | Cài và chạy không cần activation cá nhân hoặc compiler |
| Đường dẫn | Username khác, dấu/khoảng trắng, nguồn read-only | Không sửa tay source/config; không ghi vào bộ cài nguồn |
| Input | Chỉ MSI; thiếu Lang; thiếu voice.lic; sai version | Báo đúng chỗ thiếu; không commit app lỗi hoặc áp patch nhầm |
| Chọn giọng | Chỉ Aoi; chỉ Akane; cả bốn NV | Cài đúng giọng chọn, Lang phù hợp; GUI/API cùng danh sách |
| GUI | Mở lại, bốn thẻ Full version, preset, effects, xuất WAV | Không lỗi Deactivate; hành vi cần hỗ trợ chạy đúng |
| Menu cũ | Activation/trial/offline/license confirmation | Không dẫn khách vào nhánh lỗi; xử lý UX trước phát hành |
| Phát audio | GUI và Anki qua sound device thật | Khách nghe đúng câu/giọng; WAV hợp lệ chưa đủ để kết luận nghe được |
| Văn bản/giọng | こんにちは; です。; câu dài vừa đủ | Đúng UTF-8; Akane dùng Kansai, Aoi standard; đổi giọng/câu không phát cache sai |
| Anki | Cũ/mới, Add/edit/reviewer, preview/cancel/insert | Preview/cancel không sửa note; insert tạo media/tag hợp lệ |
| Không có Anki | Cài GUI rồi bổ sung Anki sau | Không chặn hoàn thành GUI; nối addon về sau thành công |
| Chạy đồng thời | GUI + Anki; nhiều yêu cầu synth | Không tranh settings/worker, không phát audio của yêu cầu khác |
| Bảo trì | Thêm/trùng/gỡ default/khôi phục giọng; update/rollback | Không cần sửa code; media Anki cũ vẫn dùng được |
| Sự cố | Hủy/lỗi copy, cổng bận, app đang mở, mất quyền ghi | Không mất công việc; resume/rollback rõ ràng, không đụng app khác |
| Gói dev | Dev mới làm bài thực hành từ docs | Build/chẩn đoán/khôi phục được mà không hỏi kiến thức ngầm |
| Clean | Audit allowlist + mở support ZIP | Không có key/prefix/collection/log cá nhân; checksum khớp |

- [ ] Ít nhất một máy hoặc VM sạch độc lập với môi trường nghiên cứu;
  xác nhận phát âm thanh thật trên máy khách thử nghiệm.
- [ ] Cài xong chạy offline, reboot, mở lại GUI/backend/Anki vẫn dùng được.
- [ ] Release notes liệt kê chính xác OS/Wine/Anki/voices đã test và hạn chế.
- [ ] Bàn giao bundle + input sources riêng + docs/dev-kit + QA report.

## 5. Thứ tự thực hiện và mốc dừng

1. P0 → P1: đóng băng baseline, giải quyết đường dẫn chung/build portable.
2. P2 → P3 → P4: cài GUI sạch, quản lý giọng, nối addon.
3. Hoàn thiện P5 xuyên suốt; P6 chỉ lấy output đã kiểm chứng.
4. P7 dùng đúng bundle; sửa lỗi rồi chạy lại nhóm ca bị ảnh hưởng.
5. Chỉ gọi bản bàn giao sẵn sàng khi mọi tiêu chí bắt buộc đạt; hạn chế
   còn lại được ghi rõ. Không coi test Xvfb là test loa vật lý.

### P8 — vntext (giai đoạn mở rộng)

Khảo sát interface extractor → connector text/playback → scheduler hữu hạn
và job/session/cancel → kiểm thử đồng thời Anki/vntext. Giữ API Anki tương
thích; câu mới chỉ thay pending job cùng session vntext. Chưa có cam kết
abort native synth. Chi tiết và tiêu chí trong
[TTS_CLIENTS_ROADMAP_VI.md](TTS_CLIENTS_ROADMAP_VI.md).

**Bước tiếp theo:** kiểm từ chính candidate đóng gói, hoàn thiện các mục
P2–P7 còn mở và QA máy khách độc lập/loa thật. P8 vntext chỉ được ghi nhận,
chưa triển khai trước khi pipeline Anki được nghiệm thu. Không sửa app cá nhân
hoặc tự gửi file ra ngoài.
