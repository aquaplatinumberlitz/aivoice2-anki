# Addon Anki: sử dụng và sửa source

Addon gọi backend HTTP, không load DLL, spawn Wine hoặc quản lý voicebank.
Nguồn API tại [aivoice2api](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/API_VI.md).
Anki-Connect không bắt buộc cho TTS.

## Dùng và cấu hình

1. Cài addon qua setup hoặc Tools → Add-ons → Install from file… với file
   .ankiaddon, rồi khởi động lại Anki.
2. Config `api_url` đúng URL backend từ runtime.json; không mặc định đoán port.
   Giữ các setting khác khi sửa URL. `voice` là id từ GET /v1/voices.
3. Trong note, nhập Nhật/romaji/nghĩa Việt theo field; addon chưa tự sinh
   romaji hoặc dịch. Chọn chữ Nhật, bấm mic, chọn giọng và nghe thử.
4. Chỉ **Đồng ý · Chèn vào card** mới lưu WAV vào media và thêm tag sound.
   Đóng dialog/preview không sửa note. Kiểm field đích và phát lại card mẫu.

Audio trong media Anki độc lập với WAV cache backend. Xóa cache hoặc gỡ
voicebank không xóa audio đã chèn. Mở Editor GUI không bắt buộc.

## Bản đồ source

| File trong developer-kit/src/anki-addon | Sửa gì |
|---|---|
| `__init__.py` | HTTP, dialog, preview/chèn media, danh sách giọng và hooks |
| `editor_compat.py`, `selection.js` | Editor cũ/mới, note id và phần chọn |
| `card_model.py` | Note type/template Nhật–Việt; giữ template khách hiện có |
| `config.json`, `config.md` | Default config và mô tả field |
| `install.py` | Build/cài .ankiaddon; xem --help trước khi dùng profile thật |

`anki/aivoice2-local.ankiaddon` và bản trong build/payload là artifact
0.2.0. Sửa source chưa tự rebuild hai file này hoặc addon trên máy khách.
Khi release addon mới cần tạo artifact và manifest mới thay vì sửa checksum
bản cũ. Hồ sơ editor/UTF-8 và smoke test ở [chỉ mục RE](ARCHIVE_INDEX_VI.md).

## Kiểm tra khi đổi addon

Backend ready và WAV mẫu hợp lệ trước; dùng note/profile thử, test chọn
chữ Nhật, nội dung vừa sửa, chọn giọng, preview không chèn, đồng ý chèn
đúng field và card phát lại. Nếu thay hỗ trợ Anki, kiểm cả editor được hỗ
trợ; không dựa vào thuộc tính Editor.nid trên phiên bản không có nó.
Không tự gửi collection, media hoặc thoại học vào báo cáo hỗ trợ.
