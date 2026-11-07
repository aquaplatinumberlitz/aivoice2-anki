# Chuẩn bị Linux cho bộ cài A.I.VOICE2

Quay lại [Quickstart A–Z](QUICKSTART_VI.md) sau khi kiểm tra bên dưới.
Các lệnh cài gói thay đổi hệ thống và hỏi mật khẩu của bạn; không chạy
start-setup.sh bằng sudo. Mở terminal trong phiên desktop của tài khoản
sẽ dùng Anki/vntext.

## Chọn đúng hệ điều hành

```bash
cat /etc/os-release
uname -m
printf 'Desktop session: %s\n' "$XDG_SESSION_TYPE"
```

Cần `x86_64`. Để có dải nổi vntext, dùng Wayland trên KDE Plasma, Sway hoặc
Hyprland; GNOME không có layer-shell. Backend và addon không đòi Rust/MinGW.
Windows native/Anki Flatpak chưa nằm trong hướng dẫn này.

## Arch / CachyOS / EndeavourOS

```bash
sudo pacman -Syu --needed python python-pyqt6 wine msitools mpv curl
```

Nếu Wine cần bật repository hoặc cấu hình theo distro, làm theo hướng dẫn
Wine của chính distro; không cài gói Ubuntu trên Arch. `mpv` là trình phát
dự phòng khi Qt Multimedia chưa có.

## Ubuntu 24.04 trở lên / distro Debian tương thích

```bash
sudo apt update
sudo apt install python3 python3-pyqt6 python3-pyqt6.qtmultimedia wine msitools mpv curl
```

Tên/phiên bản gói phụ thuộc distro và repository đã bật. Nếu apt không tìm
thấy gói, kiểm `/etc/os-release` và nguồn gói của distro trước. Không dùng
`sudo pip install` để thay Python hệ thống. Lệnh trên chỉ chuẩn bị
**backend/Anki**. Để build vntext qua kho gói chuẩn,
chọn Arch/CachyOS, Ubuntu 26.04 trở lên hoặc Debian 13: Ubuntu 24.04 thiếu
gói gtk4-layer-shell; Ubuntu 22.04 còn thiếu phiên bản GTK tối thiểu.
Xem hướng dẫn vntext trước khi chọn distro cho toàn bộ pipeline.

## Kiểm tra trước khi mở wizard

```bash
python3 -c 'from PyQt6 import QtWidgets; print("Python + Qt: OK")'
wine --version
command -v wineboot wineserver msiextract mpv
systemctl --user show-environment >/dev/null
```

Mong đợi: Qt in `OK`, Wine in version, bốn lệnh có đường dẫn và systemctl
hoàn tất không báo lỗi. Bộ cài tạo
user service qua systemd: nếu không có phiên systemd user thì cần cấu hình
khác bởi dev hỗ trợ; các lệnh trong Quickstart giả định phiên đó hoạt động.
Nếu bạn đã dùng PySide6 thay PyQt6, setup cũng hỗ trợ; kiểm bằng
`python3 -c 'from PySide6 import QtWidgets; print("Qt: OK")'`.

Anki cài theo [trang chính thức](https://apps.ankiweb.net/) và mở một lần để
tạo profile, sau đó đóng trước khi cài addon. Không cần Anki-Connect.
vntext có dependency GTK/Rust/PipeWire riêng: [hướng dẫn cài](https://github.com/aquaplatinumberlitz/vntext/blob/main/docs/INSTALL_VI.md).

Lệnh gói ở đây được kiểm tra cú pháp, không thay cho nghiệm thu mọi distro.
Môi trường chạy pipeline đã kiểm chứng là Linux x86-64/Wine; ghi lại distro,
Wine và Anki thật khi hỗ trợ để không suy rộng kết quả từ máy phát triển.
