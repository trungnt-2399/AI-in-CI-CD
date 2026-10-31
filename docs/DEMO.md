# Kịch bản demo (~15 phút)

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

## ③ @claude fix

- Trên PR kịch bản 1, comment: `@claude chỉ xoá secret và print, thêm test cho VIP50`.
- Claude sửa trên nhánh PR, chạy `flutter analyze` + `flutter test`, push commit, comment tóm tắt.
- Commit mới → CI + AI Review chạy lại trên chính bản fix của AI → người review xem diff rồi merge.

## ④ Mobile CD

```bash
./demo/run.sh 3   # tạo nhánh release/<ngày-giờ> → CD build staging
```
(hoặc Actions → **CD** → *Run workflow* → `production`, tick iOS)

- 3 job song song: *AI release notes*, *Build Android*, (*Build iOS*).
- Summary của run: "Có gì mới" + **QA checklist** Claude viết theo commit kể từ build trước.
- Tải APK ở **Artifacts**, cài lên máy thật: AppBar hiện `[staging]`.
- Merge thêm 1 PR rồi build lại → notes chỉ liệt kê thay đổi mới (nhờ tag `build/staging/<n>`).

## ⑤ Build CD fail → AI giải thích

```bash
./demo/run.sh 4      # release/demo-broken: minSdk = 16 (test vẫn pass, chỉ build native mới lỗi)
```

- CD → *Build Android* ❌ (lỗi Gradle/manifest dài, khó đọc).
- ~1–2 phút sau: tab **Issues** có issue **🚨 CD failed trên release/demo-broken** — Claude chỉ ra dòng `minSdk` trong `android/app/build.gradle.kts` và cách sửa.
- `./demo/run.sh 4fix` → CD chạy lại xanh → issue **tự đóng** kèm comment.

## Dọn dẹp

```bash
./demo/run.sh reset
```
