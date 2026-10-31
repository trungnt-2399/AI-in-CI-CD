# Kịch bản demo (~15 phút)

Chuẩn bị trước: đã push `main`, CD lần đầu đã approve, app đã lên Pages. Mở sẵn 2 tab: repo **Pull requests** và **Actions**.
Mẹo: chạy kịch bản 1–2 trước giờ seminar 5 phút để có sẵn kết quả, phòng khi mạng/AI chậm.

## ① AI Review chặn merge (3')

```bash
./demo/run.sh 1
```

- PR thêm mã `VIP50`, nhưng có: secret hard-code, `print()` lộ secret, giảm giá `subtotal/2 + 50.000` làm mọi đơn < 100.000đ thành **0đ** (miễn phí).
- Test vẫn **xanh** (không có test cho VIP50) → nhấn mạnh: *CI truyền thống không bắt được*.
- Comment **🤖 AI Code Review** liệt kê Critical → check `AI Review` ❌.
- Mở `.github/ai-review-rules.md`: *luật của team = prompt*, sửa file là đổi hành vi reviewer.

## ② AI CI Doctor (3')

```bash
./demo/run.sh 2
```

- Đổi `~/ 10` thành `~/ 100` → test `SUN10` và widget test fail.
- Sau khi CI đỏ ~1 phút, comment **🩺 AI CI Doctor**: chỉ đúng dòng gây lỗi, giải thích kỳ vọng 216.000 vs thực tế, gợi ý sửa.
- Live: sửa lại, push → CI xanh → comment tự đổi thành ✅ resolved.

## ③ CD với AI risk gate (4')

```bash
./demo/run.sh 3   # rồi merge PR
```

- Tab Actions → **CD**: job *AI risk gate* → Summary hiện bảng Rules vs AI, level **HIGH** (đổi `pubspec.yaml`).
- Job *Human approval* đang chờ → bấm **Review deployments → Approve** → deploy → smoke test.
- So sánh: merge PR kịch bản 2 (đã fix) → risk low → deploy tự động, không chờ.
- Ý chính: *AI không tự quyết deploy prod; AI phân loại để con người chỉ duyệt cái đáng duyệt.*

## ④ AI Release Notes (2')

```bash
./demo/run.sh 4 v1.1.0
```

- Tab Releases: notes chia nhóm Tính năng / Sửa lỗi / Kỹ thuật + **Store release notes VI/EN** sẵn để dán lên App Store / Google Play (nối với fastlane `release_notes`).

## Dọn dẹp

```bash
./demo/run.sh reset
```
