# FreeLicenseManager: phạm vi và hạn mức

Kiểm tra ngày 2026-11-06 trên **DLL nguyên bản trích từ MSI**, SHA-256
`10d3493f360ca6a8a8fc6138081b3e79469485197689614c2b2581f772602797`.

## Quan sát đã xác minh

Đọc metadata/CIL bằng REA, decompile hai class bằng ILSpy có sẵn, rồi gọi
trực tiếp FreeLicenseManager/feature của DLL gốc trong .NET 8.0.31 Linux.
Process chạy bubblewrap offline, không thấy home/registry cá nhân. Không sửa
DLL, không đổi LicenseManager.Current trong GUI, không cấp quyền bằng code
probe; chỉ yêu cầu feature và đọc trạng thái của implementation gốc.

| Thuộc tính | Giá trị thực tế |
| --- | --- |
| IsAuthenticated | true |
| IsEnabled | true |
| IsExpired | false |
| Type | Product |
| LimitType | Perpetual |
| MaximumExecutionCount / RemainingExecutionCount | 2147483647 |
| CurrentExecutionCount | 0 |
| StartDateTime | DateTime.MinValue |
| ExpirationDateTime | DateTime.MaxValue |
| TotalTimeSpan / RemainingTimeSpan | TimeSpan.MaxValue |

GetFeature không ràng buộc featureID trong code decompile; probe thử ID
0, 1, 42, 2147483647 và -1 đều nhận FreeLicenseFeature có trạng thái trên.
Feature.ID luôn là 0; Name giữ chuỗi truyền vào. Authenticate/Deauthenticate
không thay đổi trạng thái, IsAuthenticated vẫn true sau cả hai lời gọi.
Đây là giới hạn dạng sentinel do class báo cáo, không phải thử chạy đến
2 tỷ lần hoặc đến hết thời hạn.

FreeLicenseManager.Activate/Attach là no-op trong code đã đọc;
GetFingerPrint/GetLicense trả chuỗi rỗng. DefaultHostUri tạo Uri từ chuỗi
rỗng, có khả năng gây lỗi tùy caller/runtime; probe chưa gọi thuộc tính này.
Free manager không thay thế dịch vụ quản lý kích hoạt hoặc store license
nếu caller đòi thông tin thực từ những API đó.

## Trả lời về “full chức năng”

**Ở lớp cấp quyền này không thấy hạn mức trial, số lần dùng hoặc hạn dùng.**
Feature được báo là Product/Perpetual, enabled và authenticated. Không có
phân loại tốc độ/cao độ/âm lượng/xuất WAV thành một số tính năng free trong
hai class đã kiểm tra; mỗi GetFeature trả cùng dạng feature.

**Chưa xác minh toàn bộ GUI:** chưa chuyển GUI sang manager này và chưa test
mọi màn hình/chức năng. GUI có thể kiểm tra loại manager, feature ID/name,
cần metadata sản phẩm hoặc dùng thêm luồng Pretender/provisional license.
Do đó FreeLicenseManager là ứng viên không hạn mức cho tầng cấp quyền,
không phải bằng chứng chỉ cần chọn nó là GUI hoàn chỉnh sẽ chạy full.
File license engine/voicebank vẫn thuộc lớp native khác, đã kiểm tra riêng
trong [GUI_HEADLESS_LICENSE.md](GUI_HEADLESS_LICENSE.md).

## Evidence

- [runtime-properties.json](evidence/free-license/runtime-properties.json):
  năm feature ID, toàn bộ property và kiểm tra Authenticate/Deauthenticate.
- [FreeLicenseFeature.decompiled.cs](evidence/free-license/FreeLicenseFeature.decompiled.cs)
  và [FreeLicenseManager.decompiled.cs](evidence/free-license/FreeLicenseManager.decompiled.cs):
  ILSpy pseudocode, không phải source gốc.
- [rea-free-license.json](evidence/free-license/rea-free-license.json): REA
  metadata/CIL evidence; parent
  `ev_e8344457b459547eb6c69cf5214534a7dccbee7800a8330f666dfc3bb753fdaf`.
- [tests/free_license_probe.cs](../tests/free_license_probe.cs): probe reflection.

Runtime probe dùng .NET trên Linux, không phải tích hợp GUI Windows/Wine.
Kết quả thuộc bộ DLL 2.14.1 nêu trên; không suy rộng mọi phiên bản.
