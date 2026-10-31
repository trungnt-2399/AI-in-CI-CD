# Kịch bản demo CI (~8 phút)

Mở sẵn 2 tab: repo **Pull requests** và **Actions**.
Mẹo: chạy trước giờ seminar 5 phút để có sẵn kết quả, phòng khi mạng/AI chậm.

## ① AI Review chặn merge

```bash
./demo/run.sh 1
```

- PR thêm mã `VIP50`, nhưng có: secret hard-code, `print()` lộ secret, giảm `subtotal/2 + 50.000` làm mọi đơn < 100.000đ thành **0đ**.
- `CI` vẫn **xanh** (không có test cho VIP50) → *CI truyền thống không bắt được*.
- Comment **🤖 AI Code Review** liệt kê Critical → check `AI Review` ❌.
- Mở `.github/ai-review-rules.md`: *luật của team = prompt*, sửa file là đổi hành vi reviewer.

## ② AI CI Doctor

```bash
./demo/run.sh 2
```

- Đổi `~/ 10` thành `~/ 100` → test `SUN10` và widget test fail → `CI` ❌.
- ~1 phút sau, comment **🩺 AI CI Doctor**: chỉ đúng dòng gây lỗi, giải thích kỳ vọng 216.000 vs thực tế, gợi ý sửa.
- Live: sửa lại, push → CI xanh → comment tự đổi thành ✅ resolved.

## Dọn dẹp

```bash
./demo/run.sh reset
```
