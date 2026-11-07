# Bộ cài 0.3.0 dùng aivoice2api mặc định

Tại gốc repo hoặc thư mục giải nén bộ bàn giao:

```bash
bash start-setup.sh
```

Backend mới đã có trong build/payload/runtime, đúng version/commit/checksum
ở aivoice2api.lock.json. Máy khách không cần GitHub, compiler, tải backend
hoặc bước compose. Wizard/CLI gốc không còn cài backend WAV cũ.

## Input và cài lần đầu

MSI Editor 2.14.1 đúng baseline, Lang/voicebanks cung cấp riêng; máy có
Python 3/Qt6, Wine/msitools và Anki native nếu cài addon. Chọn root mới,
giọng và đúng addons21; đóng Anki khi cài addon. GUI và backend dùng
app/Voice + app/Lang chung, hai prefix riêng. Không clone prefix/activation.

Sau cài, kiểm đúng URL/service và WAV theo [CONNECT_VI](https://github.com/aquaplatinumberlitz/aivoice2api/blob/main/docs/CONNECT_VI.md).
Anki giữ API WAV; vntext dùng streaming nếu health công bố capability.

## Kiểm tra và đóng gói cho khách

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
python3 tools/build_release.py --output ./dist
```

Lệnh cuối tạo aivoice2-anki-0.3.0.tar.gz và checksum. Gói gồm addon/setup,
runtime mới đã build, docs và dev-kit/RE; không mang MSI, dữ liệu giọng,
license cá nhân hoặc prefix. Output có sẵn thì dùng thư mục mới.

Sau thay đổi source/artifact có chủ đích, chạy `python3 tools/build_release.py
--refresh` để tạo lại payload/release manifest và SHA256SUMS của **phiên bản
mới** rồi kiểm tra. Không dùng refresh để che corruption. Tag v0.2.0 giữ
nguyên checksum cũ; SHA256SUMS trên main nay thuộc 0.3.0.

## Dev cập nhật dependency backend

Phát hành backend ở repo aivoice2api; cập nhật lock cùng phiên bản vntext.
Tải đúng artifact, dùng tools/prepare_setup.py tạo output mới để kiểm tra:

```bash
gh release download v0.1.0 --repo aquaplatinumberlitz/aivoice2api --pattern aivoice2api-0.1.0.tar.gz --dir ./build/backend-download
python3 tools/prepare_setup.py --backend-archive ./build/backend-download/aivoice2api-0.1.0.tar.gz --output ./build/setup-new
```

Tool kiểm archive theo lock, manifest/từng file; không chạy Wine hoặc đổi
service/addon. Đưa runtime đã kiểm vào build/payload/runtime cùng manifest,
chạy test và refresh checksum bản phát hành mới. Không build worker tại
repo Anki hoặc sửa source của runtime đã đóng gói để tạo fork.

## Bản đang cài và lịch sử

Setup từ chối cài đè root hiện có. Nâng backend đã cài theo backup/verify/
receipt trong guide chung; cập nhật manager cùng lúc nếu manager còn 0.2.0.
Nút Tiếp tục khởi tạo dùng để kiểm bản cài, không là updater tự động.
Updater/uninstall toàn bộ và khả năng chịu mọi ca mất điện chưa hoàn thiện.

Bản 0.2.0 chỉ còn trong Git/tag v0.2.0; docs/RE cũ ghi đường dẫn snapshot
phải đối chiếu phiên bản. Không dùng tool build cũ để tạo backend cho khách.
