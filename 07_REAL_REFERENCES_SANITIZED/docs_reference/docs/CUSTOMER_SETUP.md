# Customer Setup

Hướng dẫn ngắn cho máy khách dùng DEB + Windows relay.

## File cần gửi

Lấy từ:

```text
00_ACTIVE/customer_package/CUSTOMER_PACKAGE_KIMIKI_SAFE_VCAMPLUS_NORED_TEST/
```

Gồm:

- File `.deb`
- File relay zip
- README/SHA256SUMS nếu cần

Không gửi:

- SSH key `.pem`
- `.env`
- DB server
- log cá nhân
- `relaykey.bin` đã login tài khoản của người khác

## Cài trên iPhone

1. Cài DEB bằng Sileo.
2. Respring nếu Sileo yêu cầu.
3. Mở icon/menu Vcam.
4. Login bằng tài khoản được cấp.

## Chạy relay trên Windows

1. Giải nén relay zip vào thư mục cố định, ví dụ:

```text
C:\VcamPlusRelay
```

2. Chạy `relay.exe`.
3. Đăng nhập bằng cùng tài khoản với DEB.
4. Để cửa sổ relay chạy.

## Cấu hình OBS

OBS stream URL:

```text
rtmp://<windows-lan-ip>/live
```

Stream key để trống.

Ví dụ nếu IP Windows là `192.168.2.144`:

```text
rtmp://192.168.2.144/live
```

## Nếu iPhone không dò được RTMP

Làm theo thứ tự:

1. Đảm bảo iPhone và Windows cùng Wi-Fi/LAN.
2. Chạy relay trước, rồi hide/mở lại menu trên iPhone.
3. Kiểm tra Windows firewall cho port `1935`.
4. Đảm bảo không có chương trình khác chiếm port `1935`.
5. Đóng relay, mở lại relay.
6. Nếu vẫn lỗi, thử chuyển network profile Windows sang Private hoặc thêm firewall rule cho relay/port 1935.

Lệnh kiểm tra port trên Windows:

```powershell
netstat -ano | findstr :1935
```

## Thứ tự dùng ổn định nhất

1. Mở relay.
2. Mở OBS và Start Streaming.
3. Mở menu iPhone.
4. Chờ hiện RTMP URL.
5. Bật LIVE.
6. Mở Camera để test.


