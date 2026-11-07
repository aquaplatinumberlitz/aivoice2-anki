# Bộ cài dùng aivoice2api

Bộ cài vẫn thuộc repo Anki. Repo backend cung cấp artifact runtime theo
`aivoice2api.lock.json`; không cần clone source vntext để dựng bộ cài.

## Tạo setup mới

Tại gốc repo Anki, tải archive đúng tag và compose:

```bash
gh release download v0.1.0 --repo aquaplatinumberlitz/aivoice2api   --pattern aivoice2api-0.1.0.tar.gz --dir ./build/backend-download
python3 tools/prepare_setup.py   --backend-archive ./build/backend-download/aivoice2api-0.1.0.tar.gz   --output ./build/setup-aivoice2api-0.1.0
bash ./build/setup-aivoice2api-0.1.0/start-setup.sh
```

Dev vừa build backend có thể trỏ --backend-archive tới file dist tương ứng;
archive phải đúng SHA-256 trong lock, không lấy file build khác commit/compiler.
Download/output đã có sẵn thì dùng thư mục mới, không chép đè để thử.
Khách được nhận cả thư mục setup đã compose và hướng dẫn input; không bắt
khách cài git/gh/MinGW. Chưa tự publish một bundle Anki 0.3.0 trong bước tách repo.

Compose kiểm checksum archive, version/commit, đường dẫn và hash từng file;
không chạy Wine, không đọc bản cài cá nhân, không đổi service hoặc addon.
Hai call site Python cũ được thích nghi để dùng kết quả Engine.speak mới;
GUI helper/patch và addon được giữ theo template bundle 0.2.0.

## Wizard và dữ liệu đầu vào

Cần MSI Editor 2.14.1 đúng baseline, Lang và voicebanks được cấp riêng;
Python 3/Qt6, Wine/msitools và Anki native nếu cài addon. Chọn root mới,
giọng cần cài và đúng addons21; đóng Anki khi cài addon. Không clone prefix
hoặc chuyển activation cá nhân cho khách. Lang/Voice nằm trong app của root,
GUI và backend dùng chung dữ liệu, hai prefix riêng.

Xem [CONNECT_VI](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/CONNECT_VI.md)
để kiểm port/service thực tế, WAV mẫu, cấu hình Anki/vntext và định nghĩa
hoàn tất. Backend chạy độc lập với Editor và các client.

## Bản 0.2.0 và bản đã cài

`bash start-setup.sh` tại gốc repo chạy bundle 0.2.0 WAV lịch sử. Các file
hash gốc giữ nguyên, kiểm bằng `sha256sum -c SHA256SUMS`. Setup compose là
thư mục mới có payload-manifest riêng; không sửa hash bundle cũ để nâng cấp.

Output compose dùng để cài vào root mới. Nó không nâng cấp root đang tồn
tại; nâng backend đã cài phải backup và triển khai có receipt theo guide
chung. Manager snapshot 0.2.0 không tương thích đầy đủ kết quả Python
Engine.speak mới; khi cần initialize/demo hãy dùng manager từ setup compose.
Không dùng manager cũ “Tiếp tục khởi tạo” để cập nhật backend.

Chưa coi updater/uninstall toàn bộ hoặc mọi ca mất điện là đã hoàn thiện.
Đọc [hỗ trợ](SUPPORT_VI.md) và phạm vi nghiệm thu gốc trước khi hứa với khách.
