#!/usr/bin/env bash
# Seminar demo scenarios. Usage: ./demo/run.sh <1|2|3|4|4fix|reset>
#   1  PR có lỗi bảo mật + logic tiền  -> AI Review báo Critical, check fail
#   2  PR làm test fail                -> CI đỏ, AI CI Doctor giải thích + gợi ý fix
#   3  Tạo nhánh release/*             -> CD build APK staging + AI viết notes/QA checklist
#   4  release/* có lỗi cấu hình Android -> CD build fail -> CI Doctor mở issue giải thích
#   4fix  sửa lại nhánh của kịch bản 4 -> CD xanh -> issue tự đóng
set -euo pipefail
cd "$(dirname "$0")/.."

scenario="${1:-}"
repo_url="$(git remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"

start_branch() {
  git diff --quiet && git diff --cached --quiet || { echo "Working tree not clean"; exit 1; }
  git checkout main && git pull --ff-only
  git checkout -B "$1"
}

open_pr() {
  local branch="$1" title="$2"
  git push -u origin "$branch" --force
  if command -v gh >/dev/null 2>&1; then
    gh pr create --base main --head "$branch" --title "$title" --body "Demo scenario $scenario" || true
  else
    echo "👉 Open PR: https://github.com/$repo_url/compare/main...$branch?expand=1"
  fi
}

case "$scenario" in
  1)
    start_branch demo/1-vip-discount
    perl -0pi -e "s/      case 'FREESHIP':/      case 'VIP50':\n        print('VIP discount applied, key=\\\$paymentSecret');\n        return subtotal ~\\/ 2 + 50000;\n      case 'FREESHIP':/" lib/cart.dart
    perl -0pi -e "s/class Product \{/const paymentSecret = 'pk_demo_9f8a7b6c5d4e3f2a1b0c';\n\nclass Product {/" lib/cart.dart
    git commit -am "feat: add VIP50 discount code"
    open_pr demo/1-vip-discount "feat: add VIP50 discount code"
    ;;
  2)
    start_branch demo/2-sun-discount
    perl -pi -e 's#return subtotal ~/ 10;#return subtotal ~/ 100; // promo reduced#' lib/cart.dart
    git commit -am "chore: reduce SUN10 promo"
    open_pr demo/2-sun-discount "chore: reduce SUN10 promo"
    ;;
  3)
    git checkout main && git pull --ff-only
    branch="release/$(date +%Y%m%d-%H%M)"
    git checkout -b "$branch"
    git push -u origin "$branch"
    echo "👉 https://github.com/$repo_url/actions/workflows/cd.yml (CD đang chạy cho $branch)"
    git checkout main
    ;;
  4)
    git checkout main && git pull --ff-only
    git checkout -B release/demo-broken
    # Lỗi chỉ lộ ra lúc build native (test/analyze vẫn pass): minSdk thấp hơn mức Flutter yêu cầu.
    perl -pi -e 's/minSdk = flutter\.minSdkVersion/minSdk = 16/' android/app/build.gradle.kts
    git commit -am "build(android): support older devices (minSdk 16)"
    git push -u origin release/demo-broken --force
    echo "👉 https://github.com/$repo_url/actions/workflows/cd.yml  rồi xem tab Issues (~10 phút)"
    git checkout main
    ;;
  4fix)
    git checkout release/demo-broken
    perl -pi -e 's/minSdk = 16/minSdk = flutter.minSdkVersion/' android/app/build.gradle.kts
    git commit -am "build(android): restore Flutter minSdk"
    git push
    echo "👉 CD chạy lại; xanh thì issue tự đóng"
    git checkout main
    ;;
  reset)
    git checkout main
    for b in demo/1-vip-discount demo/2-sun-discount release/demo-broken; do
      git branch -D "$b" 2>/dev/null || true
      git push origin --delete "$b" 2>/dev/null || true
    done
    ;;
  *)
    sed -n '2,7p' "$0"; exit 1 ;;
esac
