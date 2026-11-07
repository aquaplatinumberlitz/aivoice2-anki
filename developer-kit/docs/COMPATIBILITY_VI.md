# Phạm vi tương thích đã kiểm chứng

| Thành phần | Phiên bản/input | Trạng thái |
| --- | --- | --- |
| Editor | MSI 2.14.1, hash theo release-inputs.json | Baseline bắt buộc, không áp patch sang bản khác |
| Framework | Stock AI.Framework.License.dll | Helper .3 đã chạy GUI sạch |
| GUI snapshot | Stock 2.14.1 → patch free-ui.1 | Ẩn/chặn Deactivate, giữ card giọng, xuất WAV |
| Giọng | Akane NV, Aoi NV, Hime NV, Mikoto NV công ty cấp | Bốn giọng synth đúng; ca setup Aoi và thêm Akane đã chạy |
| Lang | Standard/Kansai từ bộ công ty cấp | Hash đúng baseline; MSI không chứa dữ liệu này |
| Linux/Wine | CachyOS x86-64, Wine 10.0-20260425 | Host nghiên cứu và namespace sạch; chưa chứng nhận distro khác |
| Anki | 26.09.3, Python 3.14.7 | Reviewer/Add/edit, Editor legacy và NewEditor đã kiểm tra |
| Âm thanh | WAV mono PCM16 48 kHz | Byte/frame/preview player hook đã kiểm tra; loa vật lý cần khách xác nhận |
| Native Anki Linux | addons21 trong thư mục data của tài khoản | Setup cho chọn đường dẫn và giữ settings |
| Flatpak/Windows native | Chưa có ma trận QA riêng | Không ghi nhãn hỗ trợ trong candidate này |

Không tự cài dependency hệ thống trên distro chưa QA. Giao gói runtime đã
build; source/compiler/tool RE thuộc dev-kit. Toolchain quan sát được ghi
trong release/toolchain-observed.json, không có nghĩa khách phải cài SDK.

Giọng legacy/galaco từng chạy trong nghiên cứu chỉ có bằng chứng từ bộ đã
cài, không nằm trong dữ liệu công ty cấp cho bản bàn giao này. Registry giữ
record dialect đã nghiên cứu. Từ 0.1.1, setup quét nguồn khách chọn và import
cả bank ngoài baseline bốn NV. Theo quy tắc người phát hành, Akane tự dùng Kansai, các giọng khác tự dùng Standard;
khả năng synth được xác minh riêng, không tự tuyên bố mọi bank đều chạy được.

vntext vẫn là roadmap sau pipeline Anki; chưa cung cấp adapter/job queue
hoặc cam kết hủy tổng hợp giữa câu.
