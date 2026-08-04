# AI Rules of Work

## Luật làm việc

1. Không đoán mò.
2. Không tự cho mình đúng.
3. Không patch binary khi chưa có input hash và expected output.
4. Không deploy khi chưa xác nhận DNS/VPS.
5. Không xoá file khi chưa backup.
6. Không in secret/token/key vào báo cáo.
7. Không kết luận lỗi iPhone nếu chưa kiểm tra relay/OBS/firewall.
8. Không kết luận lỗi server nếu chưa đọc backend log.
9. Không gửi khách bản build nếu chưa có SHA256 và test checklist.

## Luật báo cáo

Mỗi kết luận phải có dạng:

```text
Kết luận:
Bằng chứng:
Độ tin cậy: confirmed / inferred / unknown
Việc tiếp theo:
```

## Luật khi thiếu dữ kiện

Nếu thiếu dữ kiện gây thay đổi hướng làm, phải hỏi ngay. Ví dụ:

- Thiếu domain/subdomain.
- Thiếu VPS SSH.
- Thiếu bot token/admin ID.
- Thiếu file DEB/relay gốc (trong kit: `07_.../baseline_reference/`).
- Không biết artifact nào là baseline vs Kimiki final.
- Không biết URL length constraint (đọc `IDENTITY_AND_CRYPTO_CONTRACT.md` — 27 bytes).
- Không biết khách đang test thiết bị nào.
- Không biết tên systemd/nginx trên VPS (SSH verify, không đoán).

Trước khi build: tự chấm `AI_ONBOARDING_CHECKLIST.md`. Xem `HANDOFF_STATUS.md` để biết gap kit.

## Luật với production

Trước mọi thay đổi production:

1. Backup.
2. Ghi path file sẽ sửa.
3. Sửa ít nhất có thể.
4. Restart đúng service liên quan.
5. Check health/log.
6. Báo lại chính xác.



