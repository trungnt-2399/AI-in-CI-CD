#!/usr/bin/env bash
# Seminar demo scenarios (CI). Usage: ./demo/run.sh <1|2|reset>
#   1  PR có lỗi bảo mật + logic tiền  -> AI Review báo Critical, check fail
#   2  PR làm test fail                -> CI đỏ, AI CI Doctor giải thích + gợi ý fix
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
  reset)
    git checkout main
    for b in demo/1-vip-discount demo/2-sun-discount; do
      git branch -D "$b" 2>/dev/null || true
      git push origin --delete "$b" 2>/dev/null || true
    done
    ;;
  *)
    sed -n '2,4p' "$0"; exit 1 ;;
esac
