# Bài thực hành cho dev hỗ trợ mới

Mục tiêu: dùng tài liệu và input sạch để tự chẩn đoán, không dựa vào prefix
cá nhân hoặc kiến thức tác giả đang nhớ. Làm trong thư mục test riêng.

1. Đọc START_HERE, ARCHITECTURE và RUNTIME_CONFIG. Giải thích được GUI/helper
   và headless là hai đường chạy, cùng app/Voice/Lang; phân biệt activation
   cá nhân với `.lic` runtime đi kèm.
2. Trích MSI và chạy build_payload theo BUILD_AND_REPRODUCE. Kiểm hash
   helper/UI; giải thích vì sao hash input khác thì không được bỏ guard.
3. Cài chỉ Aoi vào root mới. Kiểm chỉ có app/Voice/KotonohaAoi_ns_48,
   Lang/standard. Khởi tạo và tạo WAV; mở GUI thấy đúng một giọng.
4. Thêm Akane từ dữ liệu công ty cấp. Kiểm Kansai được bổ sung, backend
   `/v1/voices` có cả hai. Synth です。 từng giọng: Akane 61.920 samples,
   Aoi 57.600 ở cấu hình worker mặc định của baseline.
5. Trên bản copy thử, tạm đưa Lang/kansai ra ngoài app. Diagnose phải nêu
   Akane incomplete, backend không liệt kê giọng thiếu Lang; khôi phục file
   đúng hash. Không làm ca phá dữ liệu trên app khách đang dùng.
6. Bật backend, thử gỡ giọng: manager phải từ chối. Dừng backend và đóng
   GUI, gỡ default rồi khôi phục. Audio đã chèn trong Anki vẫn tồn tại.
7. Tạo profile Anki test riêng, chọn câu rồi nghe thử. Đóng dialog chưa
   đồng ý phải không sửa note/media; đồng ý mới thêm tag/file. Bấm lại không
   trùng tag. Đổi câu lúc TTS đang chờ không được phát kết quả câu trước.
8. Lấy support-preview, đối chiếu không có raw log/text/license/collection;
   export ZIP và đọc nội dung. Chạy verify-files, phân biệt file ready với
   xác nhận âm thanh nghe được qua loa.
9. Lùi riêng UI patch trên bản copy, thấy nút cũ; khôi phục cặp helper/UI
   candidate và kiểm lại. Ghi rollback, không phát hành bản thử bị đổi tay.
10. Viết một báo cáo lỗi theo mẫu dưới và bổ sung link evidence khi tìm ra.

Mẫu báo cáo: môi trường/version → baseline ID/hash → thao tác tái hiện →
kết quả mong đợi/thực tế → diagnostics metadata → quan sát so với suy luận
→ thay đổi đã thử → kiểm chứng sau sửa → cách quay lại. Không đính kèm raw
license, note thật hoặc log chứa câu học nếu chưa chọn/làm sạch.

Hoàn thành khi một dev khác tái làm được các bước từ docs. Tác giả tự chạy
test không thay thế việc người mới thực sự đọc và làm bài này.
