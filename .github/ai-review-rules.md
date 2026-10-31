# Team review rules (fed to the AI reviewer)

Rules-as-code: sửa file này là thay đổi cách AI review, giống CLAUDE.md / AGENTS.md.

## Critical (chặn merge)
- Hard-coded secrets, API keys, passwords, tokens trong source.
- Logic tiền tệ sai (tính giá, giảm giá, làm tròn) hoặc có thể ra số âm.
- Crash rõ ràng: null-check `!` trên giá trị có thể null, index out of range.

## Major
- Business logic thay đổi nhưng không có test tương ứng trong `test/`.
- Dùng `print()` trong code production (dùng `debugPrint` hoặc logger).
- Gọi `setState` sau `await` mà không kiểm tra `mounted`.

## Minor
- Đặt tên không rõ nghĩa, magic number không có hằng số / comment.
- Widget lớn nên tách nhỏ, thiếu `const` constructor.

## Không cần comment
- Format / style mà `dart format` và `flutter analyze` đã bắt.
