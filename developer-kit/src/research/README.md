# Công cụ RE được giữ lại từ nghiên cứu

Các source ở đây được sao chép từ nơi từng chứa build/evidence để không bị
mất khi dọn output. Hash và vị trí gốc nằm trong provenance.json. Không có
tool nào ở đây được cài vào startup/runtime của khách.

- `voice_identity_probe.c`: worker thử **protocol cũ năm trường**, dùng
  `engine_api.h` từ `src/daemon` (`-I src/daemon` khi build). Không thay cho
  worker production bảy trường có chọn dialect.
- `gui-trace-proxy.c/.def`: proxy nghiên cứu voice/config/kana/PCM. Bản lịch
  sử còn đường dẫn output máy nghiên cứu và export forwarding theo binary
  đã kiểm chứng. Dev phải chỉnh output tới thư mục test và xác minh hash
  input trước khi dùng trên bản copy cô lập; không chép vào app khách.
- `src/daemon/poc.c` cũng là lịch sử với giả định sai, không dùng làm mẫu API.

Để hỗ trợ thông thường, dùng runtime_cli diagnose/verify-files/support ZIP
và runbook. Chỉ dùng proxy khi các bước đó chưa trả lời được câu hỏi.
