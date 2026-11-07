# Chỉ mục kết quả RE có thể dùng khi hỗ trợ

> Hồ sơ lịch sử trước 0.3.0. Source/backend và tool cũ được tra tại tag v0.2.0; hướng dẫn hiện hành ở [docs/README](../../docs/README.md).

Ngày đối chiếu: 2026-11-06. Offset/prototype chỉ có ý nghĩa với binary hash
đã ghi; không suy rộng sang bản khác. Đây là phân tích shipped artifact và
runtime đã quan sát, không phải source gốc thất lạc.

| Kết luận | Loại bằng chứng và giới hạn | Đọc tiếp |
| --- | --- | --- |
| Engine có thể chạy headless, không cần GUI/helper | Clean runtime với MSI và Lang/voice công ty cấp; không kết luận mọi voice/version | CLEAN_RUNTIME, POC_UNBLOCKED |
| Auth cần file/runtime identity đúng, talker không được tạo sau auth lỗi | Prototype và đối chứng native; NULL/thiếu lic không tương đương free mode | POC_UNBLOCKED, GUI_HEADLESS_LICENSE |
| GUI FreeLicenseManager và engine runtime license là hai lớp riêng | Thuộc tính manager + GUI sạch + test file thiếu | FREE_LICENSE_CAPABILITIES, GUI_HEADLESS_LICENSE |
| Thay helper giữ framework stock giúp GUI sạch không dùng activation cá nhân | Helper .3/build manifest và GUI review; không hứa mọi menu đã QA | FREE_CLIENT_GUIDE_VI, FREE_CLIENT_REVIEW |
| Caption activation_key rỗng làm GUI ẩn card giọng | Trước/sau UI và trace; Full version là caption, không phải key | evidence/free-client/license-list/README |
| Deactivate lỗi trước helper vì độ dài key | Trace không có deactivate, log invalid-length, metadata/assembly | FREE_CLIENT_DEACTIVATION |
| UI patch đúng snapshot 2.14.1 ẩn nút và chặn callback | Byte preconditions + callback-only runtime + GUI/WAV regression | FREE_CLIENT_DEACTIVATION, gui_patch.py |
| UTF-8 dùng encoding 0, không phải 1 | Native output + UTF-8 regression; mojibake từng tạo WAV vẫn hợp lệ | README, evidence/utf8-regression.json |
| Akane NV cần Kansai; Aoi standard | GUI trace và so PCM; không tạo khác biệt bằng effects | VOICE_IDENTITY |
| MSI không có Lang/voicebanks | msiextract list 326 file, đối chiếu thư mục dữ liệu ngoài MSI | evidence/free-client/msi-lang-inventory/result.json |
| Gỡ default và khôi phục chạy đúng trên bản thử | Native/backend lifecycle, GUI sau gỡ; không suy ra manager production đã QA mọi tình huống | evidence/voice-lifecycle/result.json |

Các tên báo cáo trên nằm trong `notes/` của source/dev-kit; dùng
[DEV_HANDOVER_INDEX_VI.md](DEV_HANDOVER_INDEX_VI.md) để mở bằng link.
Manifest input stock nằm ở `release/release-inputs.json`.

Ba identity quan trọng:

- Native engine: `711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17`.
- Framework stock: `10d3493f360ca6a8a8fc6138081b3e79469485197689614c2b2581f772602797`.
- GUI snapshot stock: `1cecf26ccecf3d6e89a6ae7a0962284fbe242cfffe3959f6a9eb052e432d5db6`.

Khi RE thêm: ghi câu hỏi → exact input/hash → phương pháp/tool version →
quan sát → suy luận → chưa biết → test đối chứng → file/evidence ID. Giữ
source proxy/probe tự viết, không chỉ giữ exe trong thư mục build/cache.

Evidence giao khách có thể đã ẩn key-like strings/path máy dev. Xem file
provenance khi có; hash output mới không thay hash raw capture nội bộ.
Không import bản đã biên tập như snapshot nguyên bản có thể replay tuyệt đối.
