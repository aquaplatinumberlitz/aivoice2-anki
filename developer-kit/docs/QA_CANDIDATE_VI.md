# Kết quả kỹ thuật và quyết định bàn giao 0.1.0

> Hồ sơ lịch sử trước 0.3.0. Source/backend và tool cũ được tra tại tag v0.2.0; hướng dẫn hiện hành ở [docs/README](../../docs/README.md).

Ngày: 2026-11-06. Kết luận: pipeline cài mới → GUI/backend → addon Anki đã
đạt các ca tự động và tích hợp dưới đây. Người dùng đã duyệt bàn giao mà
không cần thêm nghiệm thu máy khách/loa thật và không yêu cầu hoàn thiện
updater/uninstall trong đợt này. Đây là chấp nhận phạm vi/giới hạn, không
phải kết quả test bổ sung hoặc chứng nhận mọi môi trường.

| Nhóm | Kết quả |
| --- | --- |
| Baseline | 344 file khớp source stock/company-assets; không dữ liệu kích hoạt cá nhân |
| Unit | 23 ca config/install/maintenance/addon/support pass |
| GUI/engine | Hai prefix mới, offline, cùng app read-only, path có dấu; bốn giọng đúng PCM |
| Voice lifecycle | Đổi giọng/câu mới, bank chưa đăng ký, đăng ký dialect, gỡ selected/default, thiếu lic, khôi phục pass |
| Installer | Wizard chọn riêng Aoi, trích MSI, verify 326 file, patch và native check pass |
| Manager core | Thêm Akane/Kansai, gỡ default, restore và chặn khi worker chạy pass |
| Anki addon | Reviewer/Add/edit, Editor/NewEditor, preview không sửa note, insert đúng byte, không trùng tag pass |
| Audio trả muộn | Đổi text khi TTS đang chờ: kết quả cũ không phát/không chèn; cả hai editor pass |
| Integration | Giữ field config cũ và addon khác; unit độc lập trên cổng 17863 health đúng instance pass |
| Export | verify-files trên bản đã cài pass; support ZIP chỉ metadata và path redaction pass |
| Bundle | Có allowlist/hash/dev-kit; bộ trước đã QA từ archive, bản cập nhật phải giữ kết quả same-source được ghi kèm |

Bằng chứng: `notes/evidence/setup-clean/`, `delivery-p1/`, `voice-lifecycle/`,
`service-activation/`. Source dev-kit chứa test có thể tái chạy từ archive
giải nén với MSI/Lang/voicebanks cung cấp riêng, không cần home máy tác giả.

Đã chấp nhận chưa xác minh: nghe qua sound device thật (namespace không có ALSA device),
reboot trên máy khách thứ hai, Windows native/Flatpak/distro khác, mọi preset
và menu license, mất điện ở mọi pha, updater MSI/uninstall đầy đủ. Các giới
hạn này được ghi khi bàn giao. Không gọi player start hook là đã
nghe được audio vật lý. vntext chỉ là tài liệu roadmap.

Không có test nào mở collection cá nhân hoặc thay service Anki 17862 đang
dùng. Unit/prefix service smoke được tạo riêng và dọn sau phép thử.

Không chạy lại test sau quyết định duyệt. Payload runtime giữ cùng bản đã
kiểm; gói bàn giao cuối bổ sung quyết định nghiệm thu và cập nhật tài liệu.
