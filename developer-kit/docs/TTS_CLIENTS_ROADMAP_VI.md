# Backend TTS dùng cho Anki và vntext

2026-11-06. Định hướng bổ sung từ yêu cầu người dùng; **chưa triển khai
connector vntext hoặc async jobs**. vntext là tool extract text visual novel
đã có trên máy; chưa khảo sát interface nên không giả định API/plugin cụ thể.

## Quyết định kiến trúc

Giữ một dịch vụ headless A.I.VOICE2 và dữ liệu tại app/Voice/Lang. Anki và
vntext là client độc lập. Backend chỉ tổng hợp và trả audio; client quản lý
phát/dừng audio, tránh dịch vụ tự phát trùng lên hai ứng dụng.

Không viết engine mới hoặc tạo thêm một dịch vụ TTS chỉ cho vntext. Tách
logic engine, voice registry và hàng đợi khỏi HTTP handler. Giữ endpoint
Anki `POST /v1/speak` tương thích trong quá trình thêm API mới.

## Giới hạn backend hiện tại

- Có engine nóng, cache, UTF-8, registry dialect và HTTP loopback; đủ cho
  thử nghiệm một câu từ vntext nếu viết adapter gọi API.
- `POST /v1/speak` chờ trả WAV; engine xử lý tuần tự dưới lock. HTTP có thể
  tạo nhiều thread chờ lock, chưa có giới hạn hàng đợi, session/client ID,
  deadline, hủy yêu cầu hoặc quy tắc bỏ câu cũ chưa chạy.
- Ngắt kết nối HTTP không tự hủy tổng hợp. Nếu game phát text nhanh, API
  hiện tại có thể tiếp tục đọc nhiều câu đã lỗi thời. Không hứa abort native
  synthesis giữa câu khi chưa xác minh API/thread-safety.
- Cache có thể tăng không giới hạn; chưa có quota/TTL và đo p50/p95.

## Phần nên chuẩn bị ngay trong đợt bàn giao

1. Tài liệu hóa contract text/voice/WAV/error và cấu hình endpoint chung;
   Anki không phải chủ sở hữu engine hoặc nơi lưu voicebank.
2. Runtime không import aqt/Anki; connector gọi HTTP, không trực tiếp load
   DLL/đọc credential hoặc đụng prefix. Worker chỉ có một luồng synth.
3. Giữ source client adapter riêng, có thể cài vntext sau mà không cài lại
   A.I.VOICE2/giọng. Core runtime không phụ thuộc vntext để mở được.
4. Thiết kế config có version và đường dẫn chung như P1; không thêm cờ
   game/vntext riêng vào native worker khi chưa có nhu cầu thực tế.

## P8 — Mở rộng có kiểm chứng sau nền tảng P1

### A. Khảo sát vntext trên máy

- Xác định đúng app/version/path và cách xuất đoạn text hoàn chỉnh: plugin,
  event/hook, API local/socket hoặc clipboard nếu đó là interface có sẵn.
- Xác định encoding, thời điểm cập nhật từng ký tự/cả câu, tên nhân vật,
  ruby/control code, câu trùng và event khi chuyển game/session.
- Chọn đường tích hợp ổn định nhất từ interface thực tế. Chưa patch vntext
  hoặc giả định clipboard là phương án mặc định trước khi khảo sát.

### B. Adapter và hành vi phát cho visual novel

- Đợi text ổn định trong khoảng debounce cấu hình được; ưu tiên event
  complete từ extractor nếu có. Không tổng hợp lại ở mỗi ký tự cập nhật.
- Chuẩn hóa control code/ruby dựa trên format đã biết, giữ nguyên tiếng Nhật
  cần đọc. Tách tên nhân vật/câu theo tùy chọn thay vì xóa mù dấu câu.
- Loại sự kiện trùng liên tiếp trong một session, không loại vĩnh viễn một
  câu có thể được đọc lại hợp lệ khi chơi lại hoặc đổi nhân vật.
- Câu mới có request/sequence ID. Client dừng audio cũ khi cần; kết quả câu
  cũ tới muộn bị bỏ, không phát sau câu mới. Có bật/tắt tự đọc và chọn giọng.
- Mapping nhân vật → giọng là tùy chọn đợt sau khi đã có metadata đáng tin.

### C. Hàng đợi và API mở rộng

- Hàng đợi hữu hạn, trả lỗi busy rõ ràng khi đầy; request/session ID, deadline
  và trạng thái pending/running/completed/cancelled/failed.
- Anki giữ chính sách xếp hàng cho tác vụ người dùng; vntext có chế độ
  “câu mới thay câu cũ chưa chạy” **chỉ trong session của nó**. Không được
  hủy yêu cầu Anki hoặc session khác. Có fairness để không bỏ đói client.
- Pending job có thể hủy; running job ban đầu chỉ đánh dấu bỏ kết quả nếu
  native engine chưa có cơ chế abort đã kiểm chứng. Dừng audio là việc của
  client, khác với dừng synth đang chạy trong DLL.
- Bổ sung submit/status/result/cancel qua API có version; chốt tên endpoint
  khi thiết kế cụ thể. `/v1/speak` dùng cùng scheduler và vẫn trả WAV cho Anki
  cũ; không tạo hai hàng đợi điều khiển chung talker mà thiếu đồng bộ.
- Tái dùng engine nóng/cache. Thêm quota cache và dọn file không đang dùng;
  cache key tính đủ voice/dialect/config tổng hợp. Không log nguyên câu VN
  theo mặc định. Chỉ log timings, mã lỗi và request ID khi có thể.
- Đo tách thời gian chờ, tổng hợp và phát; chunk/streaming chỉ thêm nếu số
  đo chỉ ra cần thiết. Chia chunk tùy tiện có thể làm sai ngữ điệu.

### D. Nghiệm thu

- Burst nhiều câu: chỉ câu mới đúng session được đọc, không tích backlog.
- Text từng ký tự và event trùng không gây đọc lặp; tiếng Nhật đúng UTF-8.
- Đổi game/session, dừng đọc, đổi voice, extractor reconnect; kết quả cũ
  không phát nhầm. Không đụng quy trình chèn media của Anki.
- Chạy Anki và vntext đồng thời: không trộn audio, không hủy chéo, không
  gọi engine song song. Đo độ trễ trong các trường hợp cache miss/hit.
- Trường hợp game đã có lồng tiếng: khách chủ động bật/tắt TTS; không tự
  tuyên bố có thể nhận diện câu đã lồng tiếng nếu extractor không cung cấp.

## Liên hệ với plan bàn giao

P0–P7 vẫn triển khai bộ cài, quản lý giọng và Anki. P8 là mở rộng được ghi
trước để tránh ghép backend vào Anki; chưa đưa vntext vào cam kết của bản
bàn giao đầu tiên. Giới hạn scheduler phải được ghi rõ trong release notes
nếu phiên bản đầu vẫn chỉ cung cấp `/v1/speak` hiện tại.
