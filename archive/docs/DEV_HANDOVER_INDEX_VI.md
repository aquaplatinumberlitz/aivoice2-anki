# Bắt đầu đọc kỹ thuật: A.I.VOICE2 + Anki

> Hồ sơ lịch sử trước 0.3.0. Source/backend và tool cũ được tra tại tag v0.2.0; hướng dẫn hiện hành ở [docs/README](../../docs/README.md).

Giao diện Qt mới và các luồng thao tác: [MODERN_UI_VI.md](MODERN_UI_VI.md).

2026-11-06. Đây là chỉ mục tài liệu/source **đang có trong workspace**, giúp
dev mới bắt đầu. Bộ dev và tool hỗ trợ đang được đóng gói theo [DELIVERY_PLAN_VI.md](DELIVERY_PLAN_VI.md), đặc biệt P5–P7.
Đừng chép nguyên workspace này cho khách rồi coi là release sạch.

Nền tảng P0/P1 đã bắt đầu triển khai. Xem
[DELIVERY_PROGRESS_VI.md](DELIVERY_PROGRESS_VI.md) và
[RUNTIME_CONFIG_VI.md](RUNTIME_CONFIG_VI.md) trước khi dùng các mô tả lịch sử
về đường dẫn workspace/SDK cố định ở bảng bên dưới.

## Thứ tự đọc

| Bước | Đọc | Cần hiểu sau khi đọc |
| --- | --- | --- |
| 1 | [README](../README.md) và [plan bàn giao](DELIVERY_PLAN_VI.md) | Sản phẩm đang có gì, phần nào còn chưa đóng gói |
| 2 | [Hướng dẫn cơ chế Free client](../notes/FREE_CLIENT_GUIDE_VI.md) | GUI/helper/engine, hai lớp license, file nào được thay |
| 3 | [PoC đã gỡ lỗi](../notes/POC_UNBLOCKED.md) | Prototype/init/auth/load dictionary và tổng hợp đúng |
| 4 | [Nhận diện giọng](../notes/VOICE_IDENTITY.md) | Vì sao Akane/Aoi từng giống nhau; chọn Lang/dialect và evidence |
| 5 | [GUI so với headless](../notes/GUI_HEADLESS_LICENSE.md), [clean runtime](../notes/CLEAN_RUNTIME.md) | Cái gì đã chạy trên prefix mới, nguồn file và giới hạn kết luận |
| 6 | [Khả năng FreeLicenseManager](../notes/FREE_LICENSE_CAPABILITIES.md), [review GUI](../notes/FREE_CLIENT_REVIEW.md) | Thuộc tính được quan sát và các ca GUI/effects đã test |
| 7 | [Sửa Deactivate](../notes/FREE_CLIENT_DEACTIVATION.md) | Root cause, hai span patch, callback, version guard và rollback |
| 8 | [Ghi chú RE lịch sử](../notes/RE_findings.md) | Hướng điều tra cũ; phải đối chiếu với kết quả mới trước khi dùng |

Các tài liệu cũ có mô tả địa chỉ máy nghiên cứu, câu hỏi chưa đóng và giả
thuyết đã bị thay thế. Không dùng riêng một bullet cũ làm đặc tả production.
Ví dụ prototype/encoding/dialect phải theo báo cáo đã gỡ lỗi và source hiện
tại; `src/daemon/poc.c` là PoC lỗi lịch sử, không phải entry point chuẩn.

## Bản đồ source

| Source | Vai trò | Chú ý |
| --- | --- | --- |
| [server.py](https://github.com/aquaplatinumberlitz/aivoice2-anki/blob/v0.2.0/developer-kit/src/daemon/server.py) | HTTP loopback, danh sách giọng, queue/cache và worker | Dùng runtime config; registry dialect tách riêng, giữ fallback dev |
| [engine_worker.c](https://github.com/aquaplatinumberlitz/aivoice2-anki/blob/v0.2.0/developer-kit/src/daemon/engine_worker.c) | Process Wine giữ engine, chọn giọng/Lang, nhận text, ghi WAV | Không thread-safe tùy tiện; server tuần tự hóa tổng hợp |
| [engine_api.h](https://github.com/aquaplatinumberlitz/aivoice2-anki/blob/v0.2.0/developer-kit/src/daemon/engine_api.h) | Khai báo API/prototype đã dùng | Gắn với engine đã kiểm chứng, không suy rộng ABI |
| [run_auth_probe.py](https://github.com/aquaplatinumberlitz/aivoice2-anki/blob/v0.2.0/developer-kit/src/daemon/run_auth_probe.py), [auth_probe.c](https://github.com/aquaplatinumberlitz/aivoice2-anki/blob/v0.2.0/developer-kit/src/daemon/auth_probe.c) | Probe init/auth/load/synthesize và kiểm tra input | Tool dev, không thay cho setup khách; không in credential |
| [LicenseAdapter.cs](../../src/free-client/LicenseAdapter.cs) | Helper chạy qua ailm.exe, chọn FreeLicenseManager | Giữ framework stock; caption Full version không phải key |
| [gui_patch.py](../../src/free-client/gui_patch.py) | Patch UI snapshot đúng hash | Không sửa native engine; bản khác phải nghiên cứu lại |
| [build.py](../../src/free-client/build.py) | Build helper và patch GUI cùng manifest | CLI input/output và tự tìm .NET 8; xem hướng dẫn build |
| [addon](../../src/anki-addon/__init__.py) | Dialog, phát thử, chọn voice/field, chèn khi đồng ý | Không tự sinh romaji/dịch; cần backend độc lập |
| [editor_compat.py](../../src/anki-addon/editor_compat.py), [selection.js](../../src/anki-addon/selection.js) | Tương thích editor và lấy phần chọn | Khi đổi Anki phải test cả editor cũ/mới |
| [card_model.py](../../src/anki-addon/card_model.py) | Note type Nhật–Việt và template | Không thay template cũ của khách |
| [install.py](../../src/anki-addon/install.py) | Cài addon local, tạo .ankiaddon | Tool dev build/install addon; setup manager có đường dẫn chọn |

Layout khách sẽ dùng app/Voice và app/Lang làm nguồn chung. Hai bản app
trong workspace hiện tại chỉ là môi trường nghiên cứu/review; không nhân
đôi bố trí này trong release.

## Tìm bằng chứng ở đâu?

| Câu hỏi | Kết quả có thể đọc trước |
| --- | --- |
| MSI gốc có Lang không? | [Inventory MSI](../notes/evidence/free-client/msi-lang-inventory/result.json), danh sách file cùng thư mục |
| Công ty cấp bốn NV có chạy sạch không? | [Kết quả company assets](../notes/evidence/clean-runtime/company-assets/result.json), manifest/audit cùng thư mục |
| Vì sao hai giọng từng giống? | [Dialect regression](../notes/evidence/voice-identity/dialect-regression.json), các trace và đối chứng trong báo cáo giọng |
| Helper và GUI đã test gì? | [GUI review result](../notes/evidence/free-client/result.json) |
| Vì sao danh sách voice trống? | [License-list README](../notes/evidence/free-client/license-list/README.md) |
| Patch Deactivate đã chạy không? | [Kết quả UI](../notes/evidence/free-client/deactivation-ui/result.json), ảnh, WAV, trace, manifest và checksum cùng thư mục |
| Editor/UTF-8 đã sửa thế nào? | [Anki smoke](../notes/evidence/anki-gui-smoke.jsonl), [legacy](../notes/evidence/anki-gui-legacy.jsonl), [UTF-8 regression](../notes/evidence/utf8-regression.json) |

Evidence trong workspace chưa được audit để gửi hết cho khách. Release sẽ
chọn/làm sạch theo P6, giữ hash/provenance và ghi rõ những phần đã biên tập.

## Công cụ kiểm chứng hiện có

- [clean_runtime_probe.py](../tests/clean_runtime_probe.py): engine trên
  prefix/bubblewrap sạch; phân biệt input công ty cấp và bản installed cũ.
- [gui_license_probe.py](../tests/gui_license_probe.py): GUI offline cô lập;
  nhận helper/snapshot candidate. Cần PTY, JSON argv diagnostic và `quit`.
- [voice_dialect_regression.py](../tests/voice_dialect_regression.py): đối
  chiếu dialect, cần backend đúng môi trường thử.
- [anki_gui_smoke.py](../tests/anki_gui_smoke.py): profile thử, editor mặc
  định và `--legacy`; đọc prerequisites trước khi chạy.
- Các voice/style probe và proxy trace dưới tests/evidence là tool RE/dev,
  không chạy tùy tiện trên app/prefix cá nhân hoặc đưa vào startup khách.

Một số probe còn phụ thuộc cache, đường dẫn tuyệt đối hoặc toolchain đã
cài. P1/P5 phải sửa, ghi dependency và đầu ra mong đợi trước khi gọi chúng
là công cụ hỗ trợ portable. Tests nghiên cứu không tự động tương đương
với QA gói phát hành trên máy mới.

## Lộ trình cho dev hỗ trợ mới

1. Đọc sơ đồ cơ chế và nguồn input; chưa vội sửa binary khi backend lỗi.
2. Kiểm tra manifest/version, app_dir, Lang/Voice và kết nối API trước.
3. Dùng câu mẫu tổng hợp để tách lỗi engine, audio device và Anki media.
4. Đối chiếu evidence cùng binary hash; ghi điều đã quan sát và điều chưa biết.
5. Khi cần điều tra sâu, dùng bản copy/prefix cô lập và tool RE có phiên bản
   ghi lại; giữ nguyên dữ liệu/app khách và chuẩn bị rollback.
6. Bổ sung kết quả mới vào finding ledger, link evidence và cập nhật runbook.

Đợt bàn giao phải bổ sung runbook có lệnh copy/paste, đầu ra mẫu, mã lỗi,
bài thực hành và support ZIP. Chỉ mục này là điểm bắt đầu, không thay cho
các tiêu chí nghiệm thu còn mở trong plan.

Bài thực hành độc lập: [DEV_LAB_VI.md](DEV_LAB_VI.md). Phạm vi QA:
[QA_CANDIDATE_VI.md](QA_CANDIDATE_VI.md),
[COMPATIBILITY_VI.md](COMPATIBILITY_VI.md).
