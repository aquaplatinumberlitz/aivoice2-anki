# Cấu hình chung — bước P0/P1

Đây là nền tảng đang triển khai, chưa phải wizard hoặc bản phát hành khách.
GUI/backend đọc một `runtime.json`; `app_dir` chứa đúng `Voice/`, `Lang/`,
engine và các file GUI. Đường dẫn tương đối tính từ **file config**, không
từ thư mục lệnh đang chạy. Xem [mẫu](../release/runtime.example.json).

Chọn cấu hình theo thứ tự: `--config`, biến `AIVOICE2_CONFIG`, rồi
`$XDG_CONFIG_HOME/aivoice2-local/runtime.json` (mặc định `~/.config`).
Trong checkout nghiên cứu hiện có, khi không chỉ định config và chưa có
file XDG, backend giữ fallback vào app/prefix workspace để tránh làm hỏng
service cũ. Release phải dùng config tường minh; thiếu config tường minh
sẽ báo lỗi, không âm thầm dùng bản app khác.

`cache_dir` mặc định theo XDG_CACHE_HOME; `log_dir` và hai prefix theo
XDG_STATE_HOME. GUI/engine có prefix riêng và dùng cùng app. API chỉ bind
127.0.0.1, port từ config; addon phải dùng endpoint tương ứng.

## Công cụ và lệnh dev

```sh
python3 src/daemon/runtime_cli.py --config /path/to/runtime.json show-config
python3 src/daemon/runtime_cli.py --config /path/to/runtime.json diagnose
python3 src/daemon/server.py --config /path/to/runtime.json
python3 src/daemon/runtime_cli.py --config /path/to/runtime.json gui
python3 src/daemon/runtime_cli.py --config /path/to/runtime.json render-service
```

`diagnose` hiện chỉ đọc config/file/registry; không tạo prefix, chạy engine
hoặc tuyên bố đã nghe audio. `render-service` chỉ in unit cho cùng config,
không tự ghi vào systemd hoặc restart service. Unit trong source là mẫu
layout mặc định; unit service đang cài trên máy nghiên cứu chưa thay đổi.

Hai prefix phải đã được tạo mới bởi Wine/setup trước khi chạy. Launcher
chỉ thêm các drive alias V: (app), R: (runtime), O: (cache) bên trong prefix
được chỉ định, từ chối nếu alias trỏ nơi khác. Alias giúp đường dẫn Linux
có dấu/khoảng trắng không đi vào API Windows đường dẫn ANSI. Đây không
phải thay đổi mapping của prefix cá nhân. Không dùng chung prefix GUI/engine.

Worker phải được build trước:

```sh
python3 tools/build_worker.py --output-dir /path/to/runtime
python3 src/free-client/build.py --msi-app /path/to/extracted/app --output-dir /path/to/gui-build
python3 src/anki-addon/install.py --package-only --output /path/to/aivoice2-local.ankiaddon
```

Backend production không tự gọi GCC khi startup. Tool helper tự tìm .NET 8
SDK; có thể chọn Roslyn bằng `--compiler /path/to/csc.dll`. Manifest ghi hash
compiler/helper/worker và source; byte output phải được QA trước cập nhật.

Probe dev cũng nhận `--config`, `--voice`, `--probe-exe` và `--output-dir`.
Không truyền `--probe-exe` thì probe dev biên dịch `auth_probe.exe`; điều này
khác backend production luôn dùng worker có sẵn. Probe không tạo/clone prefix.

Registry tại `src/daemon/voice_registry.json` ghi Lang theo từng thư mục.
Từ 0.1.1, installer quét mọi thư mục giọng được chọn, tự chọn Kansai cho Akane và Standard cho các giọng khác (quy tắc người
phát hành xác nhận), rồi ghi registry trong runtime đã cài. `voice-imports.json` ghi gói và
hash nguồn; baseline bốn NV giữ vai trò dữ liệu tham chiếu, không là whitelist
bank. Backend vẫn loại giọng chưa đăng ký/thiếu Lang để tránh đọc sai; cách
thêm đúng là qua manager để nó đăng ký dialect và lưu provenance.

## Lập lại baseline

```sh
python3 tools/release_baseline.py \
  --msi /path/to/AIVoice2Editor.msi \
  --msi-app /path/to/extracted/app \
  --assets-dir /path/to/company-assets \
  --output release/release-inputs.json
```

Manifest chỉ chứa tên nguồn logic, path tương đối, kích thước/hash. Tool
đọc stock trích từ MSI và Lang/voicebanks công ty cấp, kiểm tra core hash
và đối chiếu dictionary/runtime license với clean-run evidence. Không đọc
prefix/Anki/sidecar DLL bên ngoài input. Không chứa nội dung `.lic` hoặc
credential. Toàn bộ input không bị thay đổi.

Baseline không thay QA distro/phiên bản Wine/Anki hoặc việc thử loa thật
trên máy mới. Các phần đó vẫn là gate P7 trong plan bàn giao.
